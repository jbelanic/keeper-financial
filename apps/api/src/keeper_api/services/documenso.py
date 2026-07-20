from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from keeper_api.core.config import Settings

_ALLOWED_STATUSES = {"DRAFT", "PENDING", "COMPLETED", "REJECTED"}
_MAX_RESPONSE_BYTES = 64 * 1024


class DocumensoError(RuntimeError):
    """A bounded, user-safe Documenso synchronization failure."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def fetch_envelope_status(settings: Settings, envelope_id: str) -> str:
    """Fetch one exact envelope and return an allow-listed Documenso status.

    Redirects are rejected so the API token cannot be forwarded to another host.
    The response is bounded and neither token nor response body is included in errors.
    """

    if settings.esign_provider != "documenso":
        raise DocumensoError("Documenso is not configured")
    if not settings.documenso_api_base_url or not settings.documenso_api_token:
        raise DocumensoError("Documenso is not configured")
    normalized_id = envelope_id.strip()
    if not normalized_id or len(normalized_id) > 255:
        raise DocumensoError("Documenso envelope identifier is invalid")
    url = f"{settings.documenso_api_base_url.rstrip('/')}/envelope/{quote(normalized_id, safe='')}"
    if urlparse(url).scheme != "https":
        raise DocumensoError("Documenso API URL must use HTTPS")
    # The configured URL is validated above and again by Settings; redirects
    # are disabled below so the authorization token cannot leave that origin.
    request = Request(  # noqa: S310
        url,
        headers={
            "Accept": "application/json",
            "Authorization": settings.documenso_api_token.get_secret_value(),
        },
        method="GET",
    )
    try:
        with build_opener(_NoRedirect).open(
            request, timeout=settings.documenso_timeout_seconds
        ) as response:
            body = response.read(_MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise DocumensoError("Documenso status could not be verified") from exc
    if len(body) > _MAX_RESPONSE_BYTES:
        raise DocumensoError("Documenso response exceeded the allowed size")
    try:
        document = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocumensoError("Documenso returned an invalid response") from exc
    if not isinstance(document, dict):
        raise DocumensoError("Documenso returned an invalid response")
    if document.get("id") != normalized_id:
        raise DocumensoError("Documenso returned a different envelope")
    status = document.get("status")
    if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
        raise DocumensoError("Documenso returned an unsupported status")
    return status


__all__ = ["DocumensoError", "fetch_envelope_status"]
