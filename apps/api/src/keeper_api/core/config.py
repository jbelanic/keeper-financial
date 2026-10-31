from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "production"]
StorageBackend = Literal["local", "s3"]
MalwareScannerBackend = Literal["clamav", "local_test", "disabled"]
# `disabled` and `manual` both mean "no provider integration": the executed
# contractor agreement is signed outside Keeper and an administrator records a
# manual attestation against the assignment's agreement gate. Only `documenso`
# hands that gate to the provider, and it is the only mode that requires the
# DOCUMENSO_* values.
EsignProvider = Literal["disabled", "manual", "documenso"]


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
    supabase_user_url: str = "http://127.0.0.1:54321/auth/v1/user"
    # Browser-visible hosted project base URL. Production identity must be either
    # the exact local CLI endpoint or an exact HTTPS .supabase.co host that
    # matches this value; see validate_tier_safety.
    next_public_supabase_url: str | None = None
    supabase_anon_key: SecretStr | None = None
    # The local web client already needs this browser-safe public key. Accepting
    # the same value avoids a second local secret-shaped setting while keeping
    # service-role credentials out of the application-start boundary.
    next_public_supabase_anon_key: SecretStr | None = None
    supabase_user_timeout_seconds: float = Field(default=5, gt=0, le=15)
    supabase_jwt_algorithms: str = "ES256"
    dev_auth_enabled: bool = True
    require_admin_mfa: bool = False

    lead_rate_limit_requests: int = Field(default=5, ge=1, le=100)
    lead_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    lead_rate_limit_tracked_clients: int = Field(default=10_000, ge=100, le=100_000)

    storage_backend: StorageBackend = "local"
    local_storage_path: Path = Path("./storage/dev_uploads")
    public_object_urls_enabled: bool = False
    max_document_bytes: int = Field(default=10 * 1024 * 1024, ge=1, le=10 * 1024 * 1024)
    allowed_document_mime_types: str = (
        "application/pdf,application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    malware_scanner_backend: MalwareScannerBackend = "local_test"
    malware_scanner_fail_closed: bool = True
    document_scan_max_concurrency: int = Field(default=4, ge=1, le=32)
    clamav_host: str = Field(default="127.0.0.1", min_length=1, max_length=253)
    clamav_port: int = Field(default=3310, ge=1, le=65535)
    clamav_connect_timeout_seconds: float = Field(default=2.0, gt=0, le=30)
    clamav_read_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    clamav_max_chunks: int = Field(default=512, ge=1, le=4096)
    clamav_max_response_bytes: int = Field(default=4096, ge=64, le=65536)
    s3_endpoint_url: str | None = None
    s3_public_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_bucket: str | None = None
    s3_region: str = "us-east-1"
    signed_url_ttl_seconds: int = Field(default=60, ge=30, le=300)

    # Origin used only to compose the stable URL of a Keeper-served public agent
    # photo (decision 56). It is never an authorization, redirect, cookie, or CORS
    # value, and it does not make MinIO or any object URL public. Production must be
    # the exact HTTPS origin; dev/test may use a loopback http origin with a port.
    public_site_base_url: str = "https://keeperfinancial.ca"
    agent_photo_max_bytes: int = Field(default=5 * 1024 * 1024, ge=1, le=5 * 1024 * 1024)

    mortgage_application_provider: str = "disabled"
    mortgage_application_url: str | None = None
    mortgage_application_allowed_hosts: str = ""
    mortgage_application_agent_links: dict[str, str] = Field(default_factory=dict)
    esign_provider: EsignProvider = "disabled"
    documenso_api_base_url: str | None = None
    documenso_public_base_url: str | None = None
    documenso_api_token: SecretStr | None = None
    documenso_timeout_seconds: float = Field(default=5.0, gt=0, le=15)
    documenso_ica_template_id: int | None = Field(default=None, gt=0)
    documenso_ica_signer_recipient_id: int | None = Field(default=None, gt=0)
    crm_provider: str = "disabled"

    borrower_application_enabled: bool = False
    borrower_real_data_enabled: bool = False
    borrower_application_origin: str = "https://apply.keeperfinancial.ca"
    borrower_encryption_keyring_file: str | None = None
    borrower_capability_hmac_key_file: str | None = None
    borrower_encryption_active_key_id: str = "v1"
    borrower_draft_inactivity_days: int = 30
    borrower_rate_limit_requests: int = Field(default=10, ge=1, le=100)
    borrower_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    borrower_rate_limit_tracked_clients: int = Field(default=10_000, ge=100, le=100_000)
    borrower_max_document_bytes: int = Field(default=25 * 1024 * 1024, ge=1, le=25 * 1024 * 1024)
    borrower_max_document_count: int = Field(default=25, ge=1, le=25)

    smtp_enabled: bool = False
    smtp_host: str = "127.0.0.1"
    smtp_port: int = Field(default=54324, ge=1, le=65535)
    smtp_from: str = "no-reply@keeperfinancial.ca"
    smtp_use_tls: bool = False
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_notification_subject: str = "A borrower application has been assigned to you"
    lead_notification_email_enabled: bool = False
    lead_notification_admin_email: str | None = None
    lead_notification_broker_email: str | None = None
    lead_notification_subject: str = "New Keeper contact request received"
    borrower_max_total_document_bytes: int = Field(
        default=250 * 1024 * 1024, ge=1, le=250 * 1024 * 1024
    )

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
        if self.supabase_anon_key is None and self.next_public_supabase_anon_key is not None:
            self.supabase_anon_key = self.next_public_supabase_anon_key
        if not self.jwt_algorithm_list or not set(self.jwt_algorithm_list).issubset(
            {"ES256", "RS256"}
        ):
            raise ValueError("SUPABASE_JWT_ALGORITHMS must use only ES256 or RS256")
        if self.public_object_urls_enabled:
            raise ValueError("public object URLs are prohibited in every environment")
        if not self.malware_scanner_fail_closed:
            raise ValueError("malware scanning must fail closed in every environment")

        public_site = urlparse(self.public_site_base_url)
        public_site_is_https_origin = (
            public_site.scheme == "https"
            and bool(public_site.hostname)
            and not public_site.username
            and not public_site.password
            and not public_site.query
            and not public_site.fragment
            and public_site.path in {"", "/"}
            and public_site.port in {None, 443}
        )
        # Dev/test composes the same stable photo URL against a loopback origin so an
        # uploaded agent photo resolves where it is actually served. Production stays
        # HTTPS-only and is additionally pinned to the live hostname below, so this
        # branch can never describe a deployed environment.
        public_site_is_local_loopback = (
            self.app_env != "production"
            and public_site.scheme == "http"
            and public_site.hostname in {"localhost", "127.0.0.1"}
            and not public_site.username
            and not public_site.password
            and not public_site.query
            and not public_site.fragment
            and public_site.path in {"", "/"}
            and public_site.port is not None
        )
        if not (public_site_is_https_origin or public_site_is_local_loopback):
            raise ValueError(
                "PUBLIC_SITE_BASE_URL must be an exact HTTPS origin with no path, "
                "credentials, port, query, or fragment; outside production a loopback "
                "http origin with an explicit port (for example http://localhost:3000) "
                "is also accepted"
            )

        if self.app_env == "production":
            errors: list[str] = []
            if self.debug:
                errors.append("DEBUG must be false")
            if self.dev_auth_enabled:
                errors.append("DEV_AUTH_ENABLED must be false")
            if not self.require_admin_mfa:
                errors.append("REQUIRE_ADMIN_MFA must be true")
            if self.storage_backend != "s3":
                errors.append("STORAGE_BACKEND must be s3")
            if self.malware_scanner_backend != "clamav":
                errors.append("live malware scanner must use clamav")
                if self.malware_scanner_backend == "local_test":
                    errors.append("local test malware scanner is prohibited")
            if self.clamav_host != "clamav" or self.clamav_port != 3310:
                errors.append("live ClamAV must use the Compose service clamav:3310")
            if "*" in self.cors_origin_list:
                errors.append("wildcard CORS is prohibited")
            for origin in [self.web_origin, *self.cors_origin_list]:
                parsed = urlparse(origin)
                if parsed.scheme != "http" or parsed.hostname not in {
                    "localhost",
                    "127.0.0.1",
                    "apply.localhost",
                }:
                    errors.append("live web origins must use local-host HTTP")
                    break
            database = urlparse(self.database_url)
            if database.scheme != "postgresql+psycopg" or database.hostname != "db":
                errors.append("live database must use psycopg and the Compose service name db")
            required = {
                "SUPABASE_ISSUER": self.supabase_issuer,
                "SUPABASE_JWKS_URL": self.supabase_jwks_url,
                "SUPABASE_USER_URL": self.supabase_user_url,
                "SUPABASE_ANON_KEY": self.supabase_anon_key,
                "S3_ENDPOINT_URL": self.s3_endpoint_url,
                "S3_PUBLIC_ENDPOINT_URL": self.s3_public_endpoint_url,
                "S3_ACCESS_KEY_ID": self.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
                "S3_BUCKET": self.s3_bucket,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                errors.append(f"required values missing: {', '.join(missing)}")
            issuer = urlparse(self.supabase_issuer)
            jwks = urlparse(self.supabase_jwks_url)
            user_endpoint = urlparse(self.supabase_user_url)
            public_base = urlparse(self.next_public_supabase_url or "")

            # Exactly two permitted identity shapes; anything else fails closed.
            # (a) The local CLI endpoint (dev/test / side-by-side).
            local_shape = (
                issuer.scheme == "http"
                and issuer.hostname in {"localhost", "127.0.0.1"}
                and issuer.port == 54321
                and issuer.path.rstrip("/") == "/auth/v1"
                and jwks.scheme == "http"
                and jwks.hostname == "host.docker.internal"
                and jwks.port == 54321
                and jwks.path == "/auth/v1/.well-known/jwks.json"
                and user_endpoint.scheme == "http"
                and user_endpoint.hostname == "host.docker.internal"
                and user_endpoint.port == 54321
                and user_endpoint.path == "/auth/v1/user"
            )

            # (b) An exact hosted Supabase HTTPS endpoint on the same host as
            # NEXT_PUBLIC_SUPABASE_URL, all three paths exact, no non-443 port.
            # The browser-facing base itself must also be HTTPS with no port,
            # credentials, query, or fragment, so an http:// public base can
            # never satisfy the hosted shape (dev/test uses the loopback base).
            hosted_host = public_base.hostname
            hosted_shape = (
                hosted_host is not None
                and hosted_host.endswith(".supabase.co")
                and public_base.scheme == "https"
                and public_base.port in {None, 443}
                and not public_base.username
                and not public_base.password
                and not public_base.query
                and not public_base.fragment
                and issuer.scheme == "https"
                and issuer.hostname == hosted_host
                and issuer.port in {None, 443}
                and issuer.path.rstrip("/") == "/auth/v1"
                and jwks.scheme == "https"
                and jwks.hostname == hosted_host
                and jwks.port in {None, 443}
                and jwks.path == "/auth/v1/.well-known/jwks.json"
                and user_endpoint.scheme == "https"
                and user_endpoint.hostname == hosted_host
                and user_endpoint.port in {None, 443}
                and user_endpoint.path == "/auth/v1/user"
            )

            if not (local_shape or hosted_shape):
                errors.append(
                    "live Supabase identity must be either the local CLI endpoint "
                    "(http loopback:54321) or an exact hosted HTTPS .supabase.co "
                    "endpoint on the same host as NEXT_PUBLIC_SUPABASE_URL"
                )
            if self.s3_endpoint_url:
                endpoint = urlparse(self.s3_endpoint_url)
                if (
                    endpoint.scheme != "http"
                    or endpoint.hostname != "minio"
                    or endpoint.port != 9000
                ):
                    errors.append("live S3 endpoint must use the MinIO Compose service")
            if self.s3_public_endpoint_url:
                public_endpoint = urlparse(self.s3_public_endpoint_url)
                if (
                    public_endpoint.scheme != "http"
                    or public_endpoint.hostname not in {"localhost", "127.0.0.1"}
                    or public_endpoint.port != 9000
                ):
                    errors.append("live signed-object endpoint must use local-host MinIO")
            if public_site.hostname != "keeperfinancial.ca":
                errors.append(
                    "PUBLIC_SITE_BASE_URL must be https://keeperfinancial.ca in the live tier"
                )
            if errors:
                raise ValueError("unsafe live Docker configuration: " + "; ".join(errors))

        if self.storage_backend == "s3":
            s3_values = [
                self.s3_endpoint_url,
                self.s3_public_endpoint_url,
                self.s3_access_key_id,
                self.s3_secret_access_key,
                self.s3_bucket,
            ]
            if not all(s3_values):
                raise ValueError(
                    "S3 storage requires internal/public endpoints, credentials, and a private bucket"
                )
        if self.esign_provider == "documenso":
            if not all(
                [
                    self.documenso_api_base_url,
                    self.documenso_public_base_url,
                    self.documenso_api_token,
                ]
            ):
                raise ValueError("Documenso requires API/public URLs and an API token")
            api = urlparse(self.documenso_api_base_url or "")
            public = urlparse(self.documenso_public_base_url or "")
            if (
                api.scheme != "https"
                or not api.hostname
                or api.username
                or api.password
                or api.query
                or api.fragment
                or api.path.rstrip("/") != "/api/v2"
            ):
                raise ValueError("Documenso API URL must be an exact HTTPS /api/v2 origin")
            if (
                public.scheme != "https"
                or public.hostname != "sign.keeperfinancial.ca"
                or public.port not in {None, 443}
                or public.username
                or public.password
                or public.query
                or public.fragment
                or public.path not in {"", "/"}
            ):
                raise ValueError(
                    "Documenso public URL must be exactly https://sign.keeperfinancial.ca"
                )

        if self.borrower_real_data_enabled and not self.borrower_application_enabled:
            raise ValueError("BORROWER_REAL_DATA_ENABLED requires BORROWER_APPLICATION_ENABLED")

        if self.borrower_application_enabled:
            if not self.borrower_encryption_keyring_file:
                raise ValueError(
                    "BORROWER_ENCRYPTION_KEYRING_FILE is required when borrower application is enabled"
                )
            if not self.borrower_capability_hmac_key_file:
                raise ValueError(
                    "BORROWER_CAPABILITY_HMAC_KEY_FILE is required when borrower application is enabled"
                )
            from pathlib import Path

            keyring_path = Path(self.borrower_encryption_keyring_file)
            hmac_path = Path(self.borrower_capability_hmac_key_file)
            if not keyring_path.exists():
                raise ValueError("BORROWER_ENCRYPTION_KEYRING_FILE must exist")
            if not hmac_path.exists():
                raise ValueError("BORROWER_CAPABILITY_HMAC_KEY_FILE must exist")
            try:
                parsed_origin = urlparse(self.borrower_application_origin)
                if not parsed_origin.scheme or not parsed_origin.hostname:
                    raise ValueError("BORROWER_APPLICATION_ORIGIN must be a valid URL")
            except ValueError:
                raise ValueError("BORROWER_APPLICATION_ORIGIN must be a valid URL") from None
            if (
                self.app_env == "production"
                and self.borrower_application_origin.rstrip("/")
                != "https://apply.keeperfinancial.ca"
            ):
                raise ValueError(
                    "BORROWER_APPLICATION_ORIGIN must be exactly "
                    "https://apply.keeperfinancial.ca in production"
                )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
