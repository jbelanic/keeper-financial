import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from keeper_api.core.config import Settings
from keeper_api.integrations.mortgage_application import (
    MortgageApplicationAdapter,
    MortgageApplicationUnavailable,
)
from keeper_api.services.storage import LocalPrivateStorage, StorageError


def configured_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "app_env": "local",
        "mortgage_application_provider": "approved_vendor",
        "mortgage_application_url": "https://apply.vendor.example/start",
        "mortgage_application_allowed_hosts": "apply.vendor.example",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_external_redirect_accepts_only_allowlisted_https_host() -> None:
    assert MortgageApplicationAdapter(configured_settings()).redirect_url() == (
        "https://apply.vendor.example/start"
    )
    with pytest.raises(MortgageApplicationUnavailable, match="HTTPS"):
        MortgageApplicationAdapter(
            configured_settings(mortgage_application_url="http://apply.vendor.example/start")
        ).redirect_url()
    with pytest.raises(MortgageApplicationUnavailable, match="allow-listed"):
        MortgageApplicationAdapter(
            configured_settings(mortgage_application_url="https://evil.example/start")
        ).redirect_url()


def test_external_redirect_rejects_query_data_and_unknown_agent() -> None:
    with pytest.raises(MortgageApplicationUnavailable, match="query"):
        MortgageApplicationAdapter(
            configured_settings(
                mortgage_application_url="https://apply.vendor.example/start?sin=no"
            )
        ).redirect_url()
    with pytest.raises(MortgageApplicationUnavailable, match="agent-specific"):
        MortgageApplicationAdapter(configured_settings()).redirect_url("unknown-agent")


def test_redirect_route_uses_only_safe_configured_agent_mapping(
    client: TestClient, settings: Settings
) -> None:
    settings.mortgage_application_provider = "approved_vendor"
    settings.mortgage_application_url = "https://apply.vendor.example/start"
    settings.mortgage_application_allowed_hosts = "apply.vendor.example"
    settings.mortgage_application_agent_links = {
        "published-agent": "https://apply.vendor.example/published-agent"
    }

    base = client.get("/api/v1/integrations/mortgage-application", follow_redirects=False)
    attributed = client.get(
        "/api/v1/integrations/mortgage-application?agent=published-agent",
        follow_redirects=False,
    )

    assert base.status_code == 307
    assert base.headers["Location"] == "https://apply.vendor.example/start"
    assert attributed.status_code == 307
    assert attributed.headers["Location"] == ("https://apply.vendor.example/published-agent")


def test_visitor_destination_and_sensitive_query_values_never_affect_redirect(
    client: TestClient, settings: Settings
) -> None:
    settings.mortgage_application_provider = "approved_vendor"
    settings.mortgage_application_url = "https://apply.vendor.example/start"
    settings.mortgage_application_allowed_hosts = "apply.vendor.example"

    response = client.get(
        "/api/v1/integrations/mortgage-application"
        "?destination=https%3A%2F%2Fevil.example%2Fsteal"
        "&name=Synthetic&email=private%40example.com&lead_id=private",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["Location"] == "https://apply.vendor.example/start"
    assert "Synthetic" not in response.headers["Location"]
    assert "private" not in response.headers["Location"]


def test_redirect_route_fails_closed_for_unknown_attribution(
    client: TestClient, settings: Settings
) -> None:
    settings.mortgage_application_provider = "approved_vendor"
    settings.mortgage_application_url = "https://apply.vendor.example/start"
    settings.mortgage_application_allowed_hosts = "apply.vendor.example"

    response = client.get(
        "/api/v1/integrations/mortgage-application?agent=unknown-agent",
        follow_redirects=False,
    )

    assert response.status_code == 503
    assert "Location" not in response.headers


@pytest.mark.parametrize(
    "agent",
    ["UPPERCASE", "agent%2Fpath", "agent%3Fprivate%3Dvalue"],
)
def test_redirect_route_rejects_unsafe_agent_grammar(
    client: TestClient, settings: Settings, agent: str
) -> None:
    response = client.get(
        f"/api/v1/integrations/mortgage-application?agent={agent}",
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "Location" not in response.headers


@pytest.mark.parametrize(
    "provider,url",
    [
        ("disabled", None),
        ("approved_vendor", "http://apply.vendor.example/start"),
        ("approved_vendor", "https://user:secret@apply.vendor.example/start"),
        ("approved_vendor", "https://apply.vendor.example/start?private=value"),
        ("approved_vendor", "https://apply.vendor.example/start#private"),
        ("approved_vendor", "https://not-allowed.example/start"),
    ],
)
def test_redirect_route_never_emits_location_when_disabled_or_unsafe(
    client: TestClient, settings: Settings, provider: str, url: str | None
) -> None:
    settings.mortgage_application_provider = provider
    settings.mortgage_application_url = url
    settings.mortgage_application_allowed_hosts = "apply.vendor.example"

    response = client.get("/api/v1/integrations/mortgage-application", follow_redirects=False)

    assert response.status_code == 503
    assert "Location" not in response.headers


def test_nonlocal_configuration_fails_closed() -> None:
    with pytest.raises(ValidationError, match="unsafe nonlocal configuration"):
        Settings(
            _env_file=None,
            app_env="production",
            debug=True,
            dev_auth_enabled=True,
            require_admin_mfa=False,
            storage_backend="local",
            cors_origins="*",
        )


def test_safe_nonlocal_configuration_is_accepted() -> None:
    settings = Settings(
        _env_file=None,
        app_env="staging_non_sensitive",
        debug=False,
        dev_auth_enabled=False,
        require_admin_mfa=True,
        web_origin="https://staging.keeper.example",
        cors_origins="https://staging.keeper.example",
        database_url="postgresql+psycopg://keeper:secret@db.keeper.example/keeper",
        supabase_issuer="https://identity.keeper.example/auth/v1",
        supabase_jwks_url="https://identity.keeper.example/auth/v1/.well-known/jwks.json",
        storage_backend="r2",
        malware_scanner_backend="disabled",
        r2_endpoint_url="https://synthetic-account.r2.cloudflarestorage.com",
        r2_access_key_id="synthetic-access-id",
        r2_secret_access_key="synthetic-secret",
        r2_bucket="keeper-staging-private",
    )
    assert settings.app_env == "staging_non_sensitive"


def test_local_storage_permission_failure_is_a_safe_storage_error(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage = LocalPrivateStorage(settings)

    def deny_mkdir(self: Path, *args: object, **kwargs: object) -> None:
        raise PermissionError("synthetic permission failure")

    monkeypatch.setattr(Path, "mkdir", deny_mkdir)
    with pytest.raises(StorageError, match="private storage write failed"):
        storage.put(io.BytesIO(b"%PDF-1.7 synthetic"), content_type="application/pdf")
