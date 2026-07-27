from __future__ import annotations

import json
from email.message import Message
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from keeper_api.core.config import Settings
from keeper_api.services import documenso
from keeper_api.services.documenso import DocumensoError, fetch_envelope_status, issue_ica_envelope


class _Response:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode()

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self._payload


class _Opener:
    def __init__(self, payload: object | None = None, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.request: Any = None

    def open(self, request: object, *, timeout: float) -> _Response:
        assert timeout == 5.0
        self.request = request
        if self.error:
            raise self.error
        return _Response(self.payload)


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="local",
        esign_provider="documenso",
        documenso_api_base_url="https://sign.keeperfinancial.ca/api/v2",
        documenso_public_base_url="https://sign.keeperfinancial.ca",
        documenso_api_token="synthetic-token",
        documenso_timeout_seconds=5.0,
        documenso_ica_template_id=42,
        documenso_ica_signer_recipient_id=7,
    )


def _issued_response(**overrides: object) -> dict[str, object]:
    response: dict[str, object] = {
        "id": "env-123",
        "type": "DOCUMENT",
        "status": "PENDING",
        "source": "TEMPLATE",
        "externalId": "keeper-onboarding-1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
        "recipients": [
            {
                "id": 700,
                "email": "candidate@example.test",
                "role": "SIGNER",
                "signingUrl": "https://sign.keeperfinancial.ca/sign/recipient-token-123",
            }
        ],
    }
    response.update(overrides)
    return response


def test_issue_ica_uses_exact_template_recipient_and_validated_signing_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[Any] = []
    responses = iter(
        [
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            _issued_response(),
        ]
    )

    class _RecordingOpener(_Opener):
        def open(self, request: Any, *, timeout: float) -> _Response:
            assert timeout == 5.0
            requests.append(request)
            return _Response(next(responses))

    monkeypatch.setattr(documenso, "build_opener", lambda _handler: _RecordingOpener())

    issued = issue_ica_envelope(
        _settings(),
        assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
        candidate_email="candidate@example.test",
        candidate_name="Candidate Name",
    )

    assert issued.envelope_id == "env-123"
    assert issued.status == "PENDING"
    assert issued.signing_url == "https://sign.keeperfinancial.ca/sign/recipient-token-123"
    assert [request.full_url for request in requests] == [
        "https://sign.keeperfinancial.ca/api/v2/template/42",
        "https://sign.keeperfinancial.ca/api/v2/template/use",
    ]
    assert [request.method for request in requests] == ["GET", "POST"]
    assert all(request.get_header("Authorization") == "synthetic-token" for request in requests)
    assert json.loads(requests[1].data) == {
        "templateId": 42,
        "recipients": [{"id": 7, "email": "candidate@example.test", "name": "Candidate Name"}],
        "distributeDocument": True,
        "externalId": "keeper-onboarding-1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
    }


def test_issue_ica_rejects_extra_template_recipient_before_distribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[Any] = []

    class _PreflightOnlyOpener(_Opener):
        def open(self, request: Any, *, timeout: float) -> _Response:
            assert timeout == 5.0
            requests.append(request)
            if request.method != "GET":
                raise AssertionError("template/use must not be called")
            return _Response(
                {
                    "id": 42,
                    "recipients": [
                        {"id": 7, "role": "SIGNER"},
                        {"id": 8, "role": "CC"},
                    ],
                }
            )

    monkeypatch.setattr(documenso, "build_opener", lambda _handler: _PreflightOnlyOpener())

    with pytest.raises(DocumensoError, match="template is incompatible"):
        issue_ica_envelope(
            _settings(),
            assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
            candidate_email="candidate@example.test",
            candidate_name="Candidate Name",
        )

    assert len(requests) == 1


@pytest.mark.parametrize(
    "issued_override",
    [
        {"type": "TEMPLATE"},
        {"source": "DOCUMENT"},
        {"externalId": "keeper-onboarding-other-assignment"},
        {
            "recipients": [
                {
                    "id": 700,
                    "email": "other@example.test",
                    "role": "SIGNER",
                    "signingUrl": "https://sign.keeperfinancial.ca/sign/env-123",
                }
            ]
        },
        {
            "recipients": [
                {
                    "id": 700,
                    "email": "candidate@example.test",
                    "role": "SIGNER",
                    "signingUrl": "https://sign.keeperfinancial.ca/sign/env-123",
                },
                {
                    "id": 701,
                    "email": "other@example.test",
                    "role": "CC",
                    "signingUrl": "https://sign.keeperfinancial.ca/sign/other",
                },
            ]
        },
    ],
)
def test_issue_ica_rejects_mismatched_issuance_provenance(
    monkeypatch: pytest.MonkeyPatch, issued_override: dict[str, object]
) -> None:
    responses = iter(
        [
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            _issued_response(**issued_override),
        ]
    )
    monkeypatch.setattr(
        documenso,
        "build_opener",
        lambda _handler: _Opener(next(responses)),
    )

    with pytest.raises(DocumensoError, match="incompatible"):
        issue_ica_envelope(
            _settings(),
            assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
            candidate_email="candidate@example.test",
            candidate_name="Candidate Name",
        )


@pytest.mark.parametrize(
    ("template_payload", "issued_payload"),
    [
        ({"id": 43, "recipients": [{"id": 7, "role": "SIGNER"}]}, None),
        ({"id": 42, "recipients": [{"id": 8, "role": "SIGNER"}]}, None),
        ({"id": 42, "recipients": [{"id": 7, "role": "VIEWER"}]}, None),
        (
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            _issued_response(id=""),
        ),
        (
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            _issued_response(
                recipients=[
                    {
                        "id": 700,
                        "email": "candidate@example.test",
                        "role": "SIGNER",
                        "signingUrl": "https://evil.example.test/sign/env-123",
                    }
                ]
            ),
        ),
        (
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            _issued_response(
                recipients=[
                    {
                        "id": 700,
                        "email": "candidate@example.test",
                        "role": "SIGNER",
                        "signingUrl": "https://sign.keeperfinancial.ca/sign/",
                    }
                ]
            ),
        ),
        (
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            _issued_response(status="DRAFT"),
        ),
        (
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            _issued_response(
                recipients=[
                    {
                        "id": 700,
                        "email": "candidate@example.test",
                        "role": "SIGNER",
                    }
                ]
            ),
        ),
    ],
)
def test_issue_ica_rejects_incompatible_template_or_response(
    monkeypatch: pytest.MonkeyPatch,
    template_payload: object,
    issued_payload: object | None,
) -> None:
    responses = iter(
        [template_payload] if issued_payload is None else [template_payload, issued_payload]
    )
    monkeypatch.setattr(
        documenso,
        "build_opener",
        lambda _handler: _Opener(next(responses)),
    )

    with pytest.raises(DocumensoError, match="incompatible"):
        issue_ica_envelope(
            _settings(),
            assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
            candidate_email="candidate@example.test",
            candidate_name="Candidate Name",
        )


def test_issue_ica_rejects_oversized_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class _OversizedResponse(_Response):
        def read(self, _limit: int) -> bytes:
            return b"{" + b"x" * (64 * 1024) + b"}"

    class _OversizedOpener(_Opener):
        def open(self, request: object, *, timeout: float) -> _OversizedResponse:
            self.request = request
            return _OversizedResponse({})

    monkeypatch.setattr(documenso, "build_opener", lambda _handler: _OversizedOpener())
    with pytest.raises(DocumensoError, match="exceeded"):
        issue_ica_envelope(
            _settings(),
            assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
            candidate_email="candidate@example.test",
            candidate_name="Candidate Name",
        )


@pytest.mark.parametrize(
    "provider_error",
    [
        URLError("provider body secret-response-body"),
        HTTPError(
            "https://sign.keeperfinancial.ca/api/v2/template/42",
            302,
            "redirect secret-response-body",
            Message(),
            None,
        ),
        TimeoutError("secret-response-body"),
    ],
)
def test_issue_ica_provider_failures_are_safe(
    monkeypatch: pytest.MonkeyPatch, provider_error: Exception
) -> None:
    monkeypatch.setattr(
        documenso,
        "build_opener",
        lambda _handler: _Opener(error=provider_error),
    )
    with pytest.raises(DocumensoError) as raised:
        issue_ica_envelope(
            _settings(),
            assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
            candidate_email="candidate@example.test",
            candidate_name="Candidate Name",
        )
    assert "synthetic-token" not in str(raised.value)
    assert "secret-response-body" not in str(raised.value)


def test_issue_ica_logs_diagnostic_on_schema_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Regression guard: a future Documenso schema drift (e.g. integer id
    # with no string envelopeId, or omitted type) must still fail closed AND
    # emit a diagnosable WARNING naming the rejected shape, not just a 503.
    drifted = {
        "id": 999,
        "status": "PENDING",
        "source": "TEMPLATE",
        "externalId": "keeper-onboarding-1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
        "recipients": [
            {
                "id": 700,
                "email": "candidate@example.test",
                "role": "SIGNER",
                "signingUrl": "https://sign.keeperfinancial.ca/sign/tok",
            }
        ],
    }
    responses = iter(
        [
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            drifted,
        ]
    )
    monkeypatch.setattr(
        documenso,
        "build_opener",
        lambda _handler: _Opener(next(responses)),
    )

    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(
        documenso._log,
        "warning",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(DocumensoError, match="incompatible"):
        issue_ica_envelope(
            _settings(),
            assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
            candidate_email="candidate@example.test",
            candidate_name="Candidate Name",
        )

    assert calls, "expected a diagnostic WARNING on schema drift"
    assert any("incompatible-envelope-or-provenance" in str(args) for args, _ in calls)
    assert any("summary:" in str(args) for args, _ in calls)


def test_issue_ica_accepts_envelope_id_string_or_envelopeid_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Documenso may return the envelope id either as `id` (str) or as
    # `envelopeId`; both must be accepted and stored.
    response = _issued_response()
    response.pop("id", None)
    response["envelopeId"] = "envelope_abc123"
    responses = iter(
        [
            {"id": 42, "recipients": [{"id": 7, "role": "SIGNER"}]},
            response,
        ]
    )
    monkeypatch.setattr(
        documenso,
        "build_opener",
        lambda _handler: _Opener(next(responses)),
    )
    issued = issue_ica_envelope(
        _settings(),
        assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
        candidate_email="candidate@example.test",
        candidate_name="Candidate Name",
    )
    assert issued.envelope_id == "envelope_abc123"
    assert issued.status == "PENDING"

    settings = _settings()
    settings.documenso_ica_template_id = None
    with pytest.raises(DocumensoError, match="not configured"):
        issue_ica_envelope(
            settings,
            assignment_id="1c9876f2-85f7-4fd2-8b13-8e18e03c82a6",
            candidate_email="candidate@example.test",
            candidate_name="Candidate Name",
        )


@pytest.mark.parametrize(
    "provider_status",
    ["DRAFT", "PENDING", "COMPLETED", "REJECTED"],
)
def test_documenso_status_is_allowlisted_and_redirects_are_disabled(
    monkeypatch: pytest.MonkeyPatch,
    provider_status: str,
) -> None:
    opener = _Opener({"id": "document/id", "status": provider_status})

    def fake_build_opener(handler: object) -> _Opener:
        assert getattr(handler, "__name__", "") == "_NoRedirect"
        return opener

    monkeypatch.setattr(documenso, "build_opener", fake_build_opener)

    status = fetch_envelope_status(_settings(), "document/id")

    assert status == provider_status
    assert opener.request.full_url.endswith("/envelope/document%2Fid")
    assert opener.request.get_header("Authorization") == "synthetic-token"


def test_documenso_unknown_status_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        documenso,
        "build_opener",
        lambda _handler: _Opener({"id": "document-1", "status": "UNRECOGNIZED"}),
    )
    with pytest.raises(DocumensoError, match="unsupported status"):
        fetch_envelope_status(_settings(), "document-1")


def test_documenso_network_failure_is_not_treated_as_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        documenso,
        "build_opener",
        lambda _handler: _Opener(error=URLError("synthetic outage")),
    )
    with pytest.raises(DocumensoError, match="could not be verified"):
        fetch_envelope_status(_settings(), "document-1")


def test_documenso_malformed_json_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class _MalformedResponse(_Response):
        def read(self, _limit: int) -> bytes:
            return b"not-json"

    class _MalformedOpener(_Opener):
        def open(self, request: object, *, timeout: float) -> _MalformedResponse:
            self.request = request
            return _MalformedResponse({})

    monkeypatch.setattr(documenso, "build_opener", lambda _handler: _MalformedOpener())
    with pytest.raises(DocumensoError, match="invalid response"):
        fetch_envelope_status(_settings(), "document-1")


def test_documenso_non_https_origin_is_rejected_before_request() -> None:
    settings = _settings()
    settings.documenso_api_base_url = "http://sign.keeperfinancial.ca/api/v2"
    with pytest.raises(DocumensoError, match="must use HTTPS"):
        fetch_envelope_status(settings, "document-1")


def test_documenso_settings_require_https_api_origin() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(
            _env_file=None,
            app_env="local",
            esign_provider="documenso",
            documenso_api_base_url="http://sign.keeperfinancial.ca/api/v2",
            documenso_public_base_url="https://sign.keeperfinancial.ca",
            documenso_api_token="synthetic-token",
        )
