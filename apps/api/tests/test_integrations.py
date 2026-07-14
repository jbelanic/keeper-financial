import pytest
from pydantic import ValidationError

from keeper_api.core.config import Settings
from keeper_api.integrations.mortgage_application import (
    MortgageApplicationAdapter,
    MortgageApplicationUnavailable,
)


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
        r2_endpoint_url="https://synthetic-account.r2.cloudflarestorage.com",
        r2_access_key_id="synthetic-access-id",
        r2_secret_access_key="synthetic-secret",
        r2_bucket="keeper-staging-private",
    )
    assert settings.app_env == "staging_non_sensitive"
