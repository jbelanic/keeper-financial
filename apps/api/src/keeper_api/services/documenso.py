from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from keeper_api.core.config import Settings

_ALLOWED_STATUSES = {"DRAFT", "PENDING", "COMPLETED", "REJECTED"}
_MAX_RESPONSE_BYTES = 64 * 1024
_MAX_ENVELOPE_ID_LENGTH = 255

_log = logging.getLogger(__name__)


def _safe_response_summary(payload: dict[str, object]) -> str:
    """Structurally describe a Documenso response without leaking PII or tokens.

    Only non-sensitive shape facts are included so a future schema drift is
    diagnosable from logs without exposing candidate emails, signing tokens,
    or response bodies.
    """
    recipients = payload.get("recipients")
    return (
        f"type={payload.get('type')!r} source={payload.get('source')!r} "
        f"status={payload.get('status')!r} "
        f"id_type={type(payload.get('id')).__name__} "
        f"has_envelope_id={isinstance(payload.get('envelopeId'), str)} "
        f"recipient_count={len(recipients) if isinstance(recipients, list) else type(recipients).__name__}"
    )


@dataclass(frozen=True)
class IssuedEnvelope:
    envelope_id: str
    status: str
    signing_url: str


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


def _request_json(settings: Settings, request: Request, failure: str) -> dict[str, Any]:
    try:
        with build_opener(_NoRedirect).open(
            request, timeout=settings.documenso_timeout_seconds
        ) as response:
            body = response.read(_MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        _log.warning("Documenso upstream request failed: %s | %s", type(exc).__name__, failure)
        raise DocumensoError(failure) from exc
    if len(body) > _MAX_RESPONSE_BYTES:
        raise DocumensoError("Documenso response exceeded the allowed size")
    try:
        document = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocumensoError("Documenso returned an invalid response") from exc
    if not isinstance(document, dict):
        raise DocumensoError("Documenso returned an invalid response")
    return document


def _authorization_headers(settings: Settings) -> dict[str, str]:
    assert settings.documenso_api_token is not None
    return {
        "Accept": "application/json",
        "Authorization": settings.documenso_api_token.get_secret_value(),
    }


def issue_ica_envelope(
    settings: Settings,
    *,
    assignment_id: str,
    candidate_email: str,
    candidate_name: str,
) -> IssuedEnvelope:
    """Instantiate the one configured ICA template for its exact signer slot."""
    if (
        settings.esign_provider != "documenso"
        or not settings.documenso_api_base_url
        or not settings.documenso_public_base_url
        or not settings.documenso_api_token
        or settings.documenso_ica_template_id is None
        or settings.documenso_ica_signer_recipient_id is None
    ):
        raise DocumensoError("Documenso contractor agreement issuance is not configured")
    api_origin = settings.documenso_api_base_url.rstrip("/")
    template_id = settings.documenso_ica_template_id
    recipient_id = settings.documenso_ica_signer_recipient_id
    headers = _authorization_headers(settings)
    template = _request_json(
        settings,
        Request(f"{api_origin}/template/{template_id}", headers=headers, method="GET"),  # noqa: S310
        "Documenso contractor agreement template could not be verified",
    )
    recipients = template.get("recipients")
    matches = (
        [item for item in recipients if isinstance(item, dict) and item.get("id") == recipient_id]
        if isinstance(recipients, list)
        else []
    )
    if (
        template.get("id") != template_id
        or not isinstance(recipients, list)
        or len(recipients) != 1
        or len(matches) != 1
        or matches[0].get("role") != "SIGNER"
    ):
        raise DocumensoError("Documenso contractor agreement template is incompatible")
    external_id = f"keeper-onboarding-{assignment_id}"
    payload = {
        "templateId": template_id,
        "recipients": [{"id": recipient_id, "email": candidate_email, "name": candidate_name}],
        "distributeDocument": True,
        "externalId": external_id,
    }
    use_headers = {**headers, "Content-Type": "application/json"}
    issued = _request_json(
        settings,
        Request(  # noqa: S310
            f"{api_origin}/template/use",
            headers=use_headers,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            method="POST",
        ),
        "Documenso contractor agreement could not be sent",
    )
    # This Documenso version returns the envelope identifier as `envelopeId`
    # (str) at the top level, while `id` is the integer document id.
    # Accept either field so the envelope id is captured regardless of which
    # the instance populates. Stratified provenance is still enforced by the
    # TEMPLATE source, externalId, recipient, and status guards below.
    envelope_id = issued.get("envelopeId")
    if not isinstance(envelope_id, str) or not envelope_id.strip():
        fallback_id = issued.get("id")
        if isinstance(fallback_id, str) and fallback_id.strip():
            envelope_id = fallback_id
    status = issued.get("status")
    response_recipients = issued.get("recipients")
    if (
        not isinstance(envelope_id, str)
        or not envelope_id.strip()
        or len(envelope_id) > _MAX_ENVELOPE_ID_LENGTH
        # `template/use` may omit `type` in this Documenso version; the
        # TEMPLATE source + externalId + recipient guards already pin
        # provenance, so accept a missing type alongside "DOCUMENT".
        or issued.get("type") not in {None, "DOCUMENT"}
        or status not in {"PENDING", "COMPLETED", "REJECTED"}
        or issued.get("source") != "TEMPLATE"
        or issued.get("externalId") != external_id
        or not isinstance(response_recipients, list)
    ):
        _log.warning(
            "Documenso contractor agreement response rejected: %s | summary: %s",
            "incompatible-envelope-or-provenance",
            _safe_response_summary(issued),
        )
        raise DocumensoError("Documenso contractor agreement response is incompatible")
    normalized_envelope_id = envelope_id.strip()
    exact = [
        item
        for item in response_recipients
        if isinstance(item, dict)
        and item.get("email") == candidate_email
        and item.get("role") == "SIGNER"
    ]
    if len(exact) != 1 or len(response_recipients) != 1:
        raise DocumensoError("Documenso contractor agreement response is incompatible")
    signing_url = exact[0].get("signingUrl")
    if not isinstance(signing_url, str) or not signing_url:
        token = exact[0].get("token")
        if not isinstance(token, str) or not token or len(token) > 255 or token.strip() != token:
            raise DocumensoError("Documenso contractor agreement response is incompatible")
        signing_url = (
            f"{settings.documenso_public_base_url.rstrip('/')}/sign/{quote(token, safe='')}"
        )
    if len(signing_url) > 2048:
        raise DocumensoError("Documenso contractor agreement response is incompatible")
    parsed_url = urlparse(signing_url)
    public = urlparse(settings.documenso_public_base_url)
    signing_path_token = parsed_url.path.removeprefix("/sign/")
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != public.hostname
        or parsed_url.port != public.port
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
        or not parsed_url.path.startswith("/sign/")
        or not signing_path_token
        or "/" in signing_path_token
    ):
        raise DocumensoError("Documenso contractor agreement response is incompatible")
    return IssuedEnvelope(normalized_envelope_id, status, signing_url)


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
        _log.warning(
            "Documenso status request failed: %s | envelope_id=%s",
            type(exc).__name__,
            normalized_id,
        )
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
        _log.warning(
            "Documenso status check returned a different envelope id: expected=%r actual=%r",
            normalized_id,
            document.get("id"),
        )
        raise DocumensoError("Documenso returned a different envelope")
    status = document.get("status")
    if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
        _log.warning(
            "Documenso returned an unsupported status: %r | envelope_id=%s",
            status,
            normalized_id,
        )
        raise DocumensoError("Documenso returned an unsupported status")
    return status


__all__ = ["DocumensoError", "IssuedEnvelope", "fetch_envelope_status", "issue_ica_envelope"]
