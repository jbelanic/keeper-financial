from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from re import Pattern
from typing import Literal

from starlette.formparsers import MultiPartParser
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("keeper_api.sensitive_upload")
_BEARER_TOKEN = re.compile(rb"Bearer [A-Za-z0-9\-._~+/]+={0,}$", re.IGNORECASE)
_BORROWER_CAPABILITY = re.compile(r"^[A-Za-z0-9_-]{43,128}$")
_BORROWER_CAPABILITY_COOKIE = "__Host-keeper-borrower-draft"


@dataclass(frozen=True)
class UploadRouteLimit:
    path_expression: Pattern[str]
    maximum_file_bytes: int
    private: bool = False
    auth_mode: Literal["bearer", "borrower_capability"] = "bearer"
    expected_host: str | None = None
    expected_origin: str | None = None

    @classmethod
    def exact(
        cls,
        path: str,
        *,
        maximum_file_bytes: int,
        private: bool = False,
        auth_mode: Literal["bearer", "borrower_capability"] = "bearer",
        expected_host: str | None = None,
        expected_origin: str | None = None,
    ) -> UploadRouteLimit:
        return cls(
            re.compile(rf"^{re.escape(path)}$"),
            maximum_file_bytes,
            private,
            auth_mode,
            expected_host,
            expected_origin,
        )

    @classmethod
    def pattern(
        cls,
        expression: str,
        *,
        maximum_file_bytes: int,
        private: bool = False,
        auth_mode: Literal["bearer", "borrower_capability"] = "bearer",
        expected_host: str | None = None,
        expected_origin: str | None = None,
    ) -> UploadRouteLimit:
        return cls(
            re.compile(expression),
            maximum_file_bytes,
            private,
            auth_mode,
            expected_host,
            expected_origin,
        )

    def matches(self, path: str) -> bool:
        return self.path_expression.fullmatch(path) is not None


def configure_multipart_spooling(maximum_file_bytes: int) -> None:
    """Keep every file admitted by the pre-parser bound in memory on Starlette 1.3."""
    if not hasattr(MultiPartParser, "spool_max_size"):
        raise RuntimeError("pinned Starlette does not expose multipart spool_max_size")
    MultiPartParser.spool_max_size = maximum_file_bytes


class SensitiveUploadMiddleware:
    """Authenticate syntax and bound sensitive multipart bodies before parsing."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        route_limits: Sequence[UploadRouteLimit],
        multipart_overhead_bytes: int,
    ) -> None:
        self.app = app
        self.route_limits = tuple(route_limits)
        self.multipart_overhead_bytes = multipart_overhead_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        route_limit = self._route_limit(scope)
        if route_limit is None:
            await self.app(scope, receive, send)
            return

        response_started = False

        async def safe_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                message = dict(message)
                message["headers"] = self._safe_headers(
                    list(message.get("headers", [])), private=route_limit.private
                )
            await send(message)

        auth_error = self._preparse_auth_error(scope, route_limit)
        if auth_error is not None:
            status_code, detail = auth_error
            logger.info(
                "sensitive upload rejected before parsing",
                extra={
                    "event": self._result_event(route_limit),
                    "result": "rejected",
                    "reason": detail,
                    "status_code": status_code,
                },
            )
            await self._json_response(
                safe_send,
                status_code=status_code,
                detail=detail,
                private=route_limit.private,
            )
            return

        maximum_body_bytes = route_limit.maximum_file_bytes + self.multipart_overhead_bytes
        if self._declared_too_large(scope, maximum_body_bytes):
            logger.info(
                "sensitive upload rejected before parsing",
                extra={
                    "event": self._result_event(route_limit),
                    "result": "rejected",
                    "reason": "request_body_too_large",
                    "status_code": 413,
                },
            )
            await self._json_response(
                safe_send,
                status_code=413,
                detail="request body is too large",
                private=route_limit.private,
            )
            return

        buffered: list[Message] = []
        total = 0
        while True:
            message = await receive()
            buffered.append(message)
            if message["type"] != "http.request":
                break
            total += len(message.get("body", b""))
            if total > maximum_body_bytes:
                logger.info(
                    "sensitive upload rejected before parsing",
                    extra={
                        "event": self._result_event(route_limit),
                        "result": "rejected",
                        "reason": "request_body_too_large",
                        "status_code": 413,
                    },
                )
                await self._json_response(
                    safe_send,
                    status_code=413,
                    detail="request body is too large",
                    private=route_limit.private,
                )
                return
            if not message.get("more_body", False):
                break

        index = 0

        async def replay_receive() -> Message:
            nonlocal index
            if index < len(buffered):
                message = buffered[index]
                index += 1
                return message
            return await receive()

        try:
            await self.app(scope, replay_receive, safe_send)
        except Exception:
            if response_started:
                raise
            logger.exception("unexpected sensitive upload failure")
            await self._json_response(
                safe_send,
                status_code=500,
                detail="internal server error",
                private=route_limit.private,
            )
            # Preserve normal ASGI/TestClient exception reporting after safely emitting
            # the response. ServerErrorMiddleware observes that a response has started.
            raise

    def _route_limit(self, scope: Scope) -> UploadRouteLimit | None:
        if scope["type"] != "http" or scope.get("method") != "POST":
            return None
        path = str(scope.get("path", ""))
        return next((item for item in self.route_limits if item.matches(path)), None)

    @staticmethod
    def _result_event(route_limit: UploadRouteLimit) -> str:
        if route_limit.auth_mode == "borrower_capability":
            return "borrower_document_upload_result"
        return "sensitive_upload_result"

    @staticmethod
    def _has_well_formed_bearer(scope: Scope) -> bool:
        values = [
            value for name, value in scope.get("headers", []) if name.lower() == b"authorization"
        ]
        return len(values) == 1 and _BEARER_TOKEN.fullmatch(values[0]) is not None

    @classmethod
    def _preparse_auth_error(
        cls, scope: Scope, route_limit: UploadRouteLimit
    ) -> tuple[int, str] | None:
        if route_limit.auth_mode == "bearer":
            if cls._has_well_formed_bearer(scope):
                return None
            return 401, "authentication required"

        cookie_values = [
            value.decode("latin-1")
            for name, value in scope.get("headers", [])
            if name.lower() == b"cookie"
        ]
        capabilities = []
        for cookie_header in cookie_values:
            for part in cookie_header.split(";"):
                name, separator, value = part.strip().partition("=")
                if separator and name == _BORROWER_CAPABILITY_COOKIE:
                    capabilities.append(value)
        if len(capabilities) != 1 or not _BORROWER_CAPABILITY.fullmatch(capabilities[0]):
            return 401, "authentication required"

        def header_values(header_name: bytes) -> list[str]:
            return [
                value.decode("latin-1")
                for name, value in scope.get("headers", [])
                if name.lower() == header_name
            ]

        host_values = header_values(b"host")
        origin_values = header_values(b"origin")
        csrf_values = header_values(b"x-keeper-borrower-csrf")
        if len(host_values) != 1 or len(origin_values) != 1 or len(csrf_values) != 1:
            return 403, "forbidden"
        host = host_values[0]
        if route_limit.expected_host is not None and (
            host.split(":", 1)[0].casefold()
            != route_limit.expected_host.split(":", 1)[0].casefold()
        ):
            return 403, "forbidden"
        if (
            route_limit.expected_origin is not None
            and origin_values[0] != route_limit.expected_origin
        ):
            return 403, "forbidden"
        if csrf_values[0] != "1":
            return 403, "forbidden"
        return None

    @staticmethod
    def _declared_too_large(scope: Scope, maximum: int) -> bool:
        values = [
            value for name, value in scope.get("headers", []) if name.lower() == b"content-length"
        ]
        if not values:
            return False
        if len(values) != 1:
            return True
        try:
            declared = int(values[0])
        except ValueError:
            return True
        return declared < 0 or declared > maximum

    @staticmethod
    def _safe_headers(
        headers: list[tuple[bytes, bytes]], *, private: bool
    ) -> list[tuple[bytes, bytes]]:
        blocked = {b"cache-control", b"x-content-type-options"}
        safe = [(name, value) for name, value in headers if name.lower() not in blocked]
        safe.extend(
            [
                (b"cache-control", b"private, no-store" if private else b"no-store"),
                (b"x-content-type-options", b"nosniff"),
            ]
        )
        return safe

    @classmethod
    async def _json_response(
        cls,
        send: Send,
        *,
        status_code: int,
        detail: str,
        private: bool,
    ) -> None:
        body = json.dumps({"detail": detail}, separators=(",", ":")).encode()
        headers = cls._safe_headers(
            [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
            private=private,
        )
        await send({"type": "http.response.start", "status": status_code, "headers": headers})
        await send({"type": "http.response.body", "body": body})
