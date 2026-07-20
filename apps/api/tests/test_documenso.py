from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError

import pytest

from keeper_api.core.config import Settings
from keeper_api.services import documenso
from keeper_api.services.documenso import DocumensoError, fetch_envelope_status


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
