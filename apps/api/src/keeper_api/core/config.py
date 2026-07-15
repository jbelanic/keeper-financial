from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "staging_non_sensitive", "production"]
StorageBackend = Literal["local", "r2"]
MalwareScannerBackend = Literal["local_test", "disabled"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore", hide_input_in_errors=True
    )

    app_env: Environment = "local"
    app_name: str = "Keeper Financial API"
    debug: bool = False
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    web_origin: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://keeper:keeper_local_only@localhost:5432/keeper"

    supabase_issuer: str = "http://127.0.0.1:54321/auth/v1"
    supabase_audience: str = "authenticated"
    supabase_jwks_url: str = "http://127.0.0.1:54321/auth/v1/.well-known/jwks.json"
    supabase_jwt_algorithms: str = "ES256"
    dev_auth_enabled: bool = True
    require_admin_mfa: bool = False

    lead_rate_limit_requests: int = Field(default=5, ge=1, le=100)
    lead_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    lead_rate_limit_tracked_clients: int = Field(default=10_000, ge=100, le=100_000)

    storage_backend: StorageBackend = "local"
    local_storage_path: Path = Path("./storage/dev_uploads")
    public_object_urls_enabled: bool = False
    max_document_bytes: int = 10 * 1024 * 1024
    allowed_document_mime_types: str = (
        "application/pdf,application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    malware_scanner_backend: MalwareScannerBackend = "local_test"
    r2_endpoint_url: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: SecretStr | None = None
    r2_bucket: str | None = None
    r2_region: str = "auto"
    signed_url_ttl_seconds: int = Field(default=60, ge=30, le=300)

    mortgage_application_provider: str = "disabled"
    mortgage_application_url: str | None = None
    mortgage_application_allowed_hosts: str = ""
    mortgage_application_agent_links: dict[str, str] = Field(default_factory=dict)
    esign_provider: str = "disabled"
    crm_provider: str = "disabled"

    @field_validator("mortgage_application_agent_links", mode="before")
    @classmethod
    def parse_agent_links(cls, value: object) -> object:
        if isinstance(value, str):
            return json.loads(value)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def jwt_algorithm_list(self) -> list[str]:
        return [item.strip() for item in self.supabase_jwt_algorithms.split(",") if item.strip()]

    @property
    def allowed_mortgage_hosts(self) -> set[str]:
        return {
            host.strip().lower()
            for host in self.mortgage_application_allowed_hosts.split(",")
            if host.strip()
        }

    @property
    def allowed_mime_types(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.allowed_document_mime_types.split(",")
            if item.strip()
        }

    @model_validator(mode="after")
    def validate_tier_safety(self) -> Self:
        if not self.jwt_algorithm_list or not set(self.jwt_algorithm_list).issubset(
            {"ES256", "RS256"}
        ):
            raise ValueError("SUPABASE_JWT_ALGORITHMS must use only ES256 or RS256")
        if self.public_object_urls_enabled:
            raise ValueError("public object URLs are prohibited in every environment")

        if self.app_env != "local":
            errors: list[str] = []
            if self.debug:
                errors.append("DEBUG must be false")
            if self.dev_auth_enabled:
                errors.append("DEV_AUTH_ENABLED must be false")
            if not self.require_admin_mfa:
                errors.append("REQUIRE_ADMIN_MFA must be true")
            if self.storage_backend != "r2":
                errors.append("STORAGE_BACKEND must be r2")
            if self.malware_scanner_backend == "local_test":
                errors.append("local test malware scanner is prohibited")
            if "*" in self.cors_origin_list:
                errors.append("wildcard CORS is prohibited")
            for origin in [self.web_origin, *self.cors_origin_list]:
                parsed = urlparse(origin)
                if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                    errors.append("loopback origins are prohibited")
                    break
                if parsed.scheme != "https":
                    errors.append("nonlocal origins must use HTTPS")
                    break
            database = urlparse(self.database_url)
            if not database.scheme.startswith("postgresql") or database.hostname in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                errors.append("nonlocal database must be a non-loopback PostgreSQL endpoint")
            required = {
                "SUPABASE_ISSUER": self.supabase_issuer,
                "SUPABASE_JWKS_URL": self.supabase_jwks_url,
                "R2_ENDPOINT_URL": self.r2_endpoint_url,
                "R2_ACCESS_KEY_ID": self.r2_access_key_id,
                "R2_SECRET_ACCESS_KEY": self.r2_secret_access_key,
                "R2_BUCKET": self.r2_bucket,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                errors.append(f"required values missing: {', '.join(missing)}")
            if any(
                "127.0.0.1" in value or "localhost" in value
                for value in (self.supabase_issuer, self.supabase_jwks_url)
            ):
                errors.append("local Supabase endpoints are prohibited")
            if any(
                urlparse(value).scheme != "https"
                for value in (self.supabase_issuer, self.supabase_jwks_url)
            ):
                errors.append("nonlocal Supabase endpoints must use HTTPS")
            if self.r2_endpoint_url:
                r2_endpoint = urlparse(self.r2_endpoint_url)
                if r2_endpoint.scheme != "https" or r2_endpoint.hostname in {
                    "localhost",
                    "127.0.0.1",
                    "::1",
                }:
                    errors.append("nonlocal R2 endpoint must be non-loopback HTTPS")
            if errors:
                raise ValueError("unsafe nonlocal configuration: " + "; ".join(errors))

        if self.storage_backend == "r2":
            r2_values = [
                self.r2_endpoint_url,
                self.r2_access_key_id,
                self.r2_secret_access_key,
                self.r2_bucket,
            ]
            if not all(r2_values):
                raise ValueError("R2 storage requires endpoint, credentials, and a private bucket")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
