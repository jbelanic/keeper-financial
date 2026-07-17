from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from keeper_api.middleware.sensitive_uploads import (
    SensitiveUploadMiddleware,
    UploadRouteLimit,
)

Scope = dict[str, Any]
Message = dict[str, Any]


def _scope(path: str, headers: list[tuple[bytes, bytes]]) -> Scope:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }


def _run_middleware(
    *,
    path: str = "/api/v1/upload-document",
    headers: list[tuple[bytes, bytes]],
    incoming: list[Message],
) -> tuple[list[Message], int, int]:
    received = 0
    downstream_calls = 0
    sent: list[Message] = []

    async def receive() -> Message:
        nonlocal received
        received += 1
        if not incoming:
            raise AssertionError("middleware read beyond supplied request messages")
        return incoming.pop(0)

    async def send(message: Message) -> None:
        sent.append(message)

    async def downstream(
        _scope: Scope,
        replay_receive: Callable[[], Awaitable[Message]],
        downstream_send: Callable[[Message], Awaitable[None]],
    ) -> None:
        nonlocal downstream_calls
        downstream_calls += 1
        body = bytearray()
        while True:
            message = await replay_receive()
            body.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        await downstream_send(
            {"type": "http.response.start", "status": 204, "headers": []}
        )
        await downstream_send({"type": "http.response.body", "body": bytes(body)})

    middleware = SensitiveUploadMiddleware(
        downstream,
        route_limits=(
            UploadRouteLimit.exact("/api/v1/upload-document", maximum_file_bytes=8),
            UploadRouteLimit.pattern(
                r"^/api/v1/candidate/applications/[^/]+/documents$",
                maximum_file_bytes=16,
                private=True,
            ),
        ),
        multipart_overhead_bytes=4,
    )
    asyncio.run(middleware(_scope(path, headers), receive, send))
    return sent, received, downstream_calls


@pytest.mark.parametrize(
    "authorization",
    [None, b"", b"Basic abc", b"Bearer", b"Bearer bad token", b"Bearer one, Bearer two"],
)
def test_sensitive_upload_auth_header_gate_rejects_without_reading_body(
    authorization: bytes | None,
) -> None:
    headers = [] if authorization is None else [(b"authorization", authorization)]
    incoming = [{"type": "http.request", "body": b"must-not-be-read", "more_body": False}]

    sent, received, downstream_calls = _run_middleware(headers=headers, incoming=incoming)

    assert received == 0
    assert downstream_calls == 0
    assert sent[0]["status"] == 401
    response_headers = dict(sent[0]["headers"])
    assert response_headers[b"cache-control"] == b"no-store"
    assert response_headers[b"x-content-type-options"] == b"nosniff"
    assert json.loads(sent[1]["body"]) == {"detail": "authentication required"}


def test_sensitive_upload_declared_overage_is_rejected_without_reading_or_downstream() -> None:
    sent, received, downstream_calls = _run_middleware(
        headers=[
            (b"authorization", b"Bearer syntactically-valid"),
            (b"content-length", b"13"),
        ],
        incoming=[{"type": "http.request", "body": b"not-read", "more_body": False}],
    )

    assert received == 0
    assert downstream_calls == 0
    assert sent[0]["status"] == 413


def test_sensitive_upload_chunked_overage_is_rejected_before_downstream() -> None:
    sent, received, downstream_calls = _run_middleware(
        headers=[(b"authorization", b"Bearer syntactically-valid")],
        incoming=[
            {"type": "http.request", "body": b"12345678", "more_body": True},
            {"type": "http.request", "body": b"12345", "more_body": False},
        ],
    )

    assert received == 2
    assert downstream_calls == 0
    assert sent[0]["status"] == 413
    assert dict(sent[0]["headers"])[b"x-content-type-options"] == b"nosniff"


def test_sensitive_upload_replays_bounded_chunks_only_after_complete_body() -> None:
    sent, received, downstream_calls = _run_middleware(
        headers=[(b"authorization", b"Bearer syntactically-valid")],
        incoming=[
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"5678", "more_body": False},
        ],
    )

    assert received == 2
    assert downstream_calls == 1
    assert sent[0]["status"] == 204
    assert sent[1]["body"] == b"12345678"


def test_candidate_upload_rejection_uses_private_no_store() -> None:
    sent, _, _ = _run_middleware(
        path="/api/v1/candidate/applications/id/documents",
        headers=[],
        incoming=[{"type": "http.request", "body": b"unread", "more_body": False}],
    )

    assert dict(sent[0]["headers"])[b"cache-control"] == b"private, no-store"
