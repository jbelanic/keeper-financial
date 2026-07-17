import tomllib
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SUPABASE_CONFIG_PATH = PROJECT_ROOT / "supabase" / "config.toml"


def load_supabase_config() -> dict[str, object]:
    with SUPABASE_CONFIG_PATH.open("rb") as config_file:
        return tomllib.load(config_file)


def test_supabase_config_is_local_auth_only_with_es256_mfa() -> None:
    config = load_supabase_config()

    assert config["project_id"] == "keeper-financial"
    assert config["api"] == {
        "enabled": True,
        "port": 54321,
        "schemas": ["public"],
        "extra_search_path": ["public", "extensions"],
        "max_rows": 1000,
    }
    assert config["db"]["port"] == 54322
    assert config["db"]["shadow_port"] == 54320
    assert config["db"]["pooler"]["enabled"] is False
    assert config["db"]["migrations"]["enabled"] is False
    assert config["db"]["seed"]["enabled"] is False

    auth = config["auth"]
    assert auth["enabled"] is True
    assert auth["signing_keys_path"] == "./signing_keys.json"
    assert auth["enable_signup"] is True
    assert auth["enable_anonymous_sign_ins"] is False
    assert auth["minimum_password_length"] == 12
    assert auth["email"]["enable_signup"] is True
    assert auth["email"]["enable_confirmations"] is True
    assert auth["sms"]["enable_signup"] is False
    assert auth["mfa"]["totp"] == {
        "enroll_enabled": True,
        "verify_enabled": True,
    }

    assert config["local_smtp"]["enabled"] is True
    assert config["local_smtp"]["port"] == 54324
    assert config["realtime"]["enabled"] is False

    # Studio is allowed only as local operator tooling. It is not an
    # application dependency and must remain bound to the approved local port.
    assert config["studio"] == {
        "enabled": True,
        "port": 54323,
        "api_url": "http://127.0.0.1",
    }

    # Supabase Storage remains disabled. MinIO is the only approved application
    # object store, and the S3 protocol must not be enabled as an alternate path.
    assert config["storage"]["enabled"] is False
    assert config["storage"]["s3_protocol"]["enabled"] is False
    assert config["storage"]["analytics"]["enabled"] is False
    assert config["storage"]["vector"]["enabled"] is False

    assert config["edge_runtime"]["enabled"] is False
    assert config["analytics"]["enabled"] is False


def test_supabase_redirects_are_exact_loopback_urls() -> None:
    auth = load_supabase_config()["auth"]

    assert auth["site_url"] == "http://localhost:3000"
    assert auth["additional_redirect_urls"] == [
        "http://localhost:3000/auth/callback",
        "http://127.0.0.1:3000/auth/callback",
    ]
    for raw_url in [auth["site_url"], *auth["additional_redirect_urls"]]:
        url = urlparse(raw_url)
        assert url.scheme == "http"
        assert url.hostname in {"localhost", "127.0.0.1"}
        assert url.port == 3000
        assert not url.query
        assert not url.fragment


def test_supabase_es256_signing_key_file_is_ignored() -> None:
    ignore_rules = (PROJECT_ROOT / ".gitignore").read_text().splitlines()

    assert "/supabase/signing_keys.json" in ignore_rules


def test_compose_pins_real_immutable_minio_server_release() -> None:
    compose = (PROJECT_ROOT / "compose.yaml").read_text()
    minio_service = compose.split("\n  minio:\n", maxsplit=1)[1].split(
        "\n  minio-init:\n", maxsplit=1
    )[0]

    assert "image: quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z" in minio_service
    assert "quay.io/minio/minio:latest" not in minio_service


def test_compose_uses_supported_minio_cors_configuration() -> None:
    compose = (PROJECT_ROOT / "compose.yaml").read_text()
    minio_service = compose.split("\n  minio:\n", maxsplit=1)[1].split(
        "\n  minio-init:\n", maxsplit=1
    )[0]
    minio_init_service = compose.split("\n  minio-init:\n", maxsplit=1)[1].split(
        "\n  api:\n", maxsplit=1
    )[0]

    assert "MINIO_API_CORS_ALLOW_ORIGIN: http://localhost:3000" in minio_service
    assert "mc cors set" not in minio_init_service
    assert not (PROJECT_ROOT / "infrastructure" / "minio" / "cors.xml").exists()


def test_compose_uses_the_db_service_for_the_api_database_url() -> None:
    compose = (PROJECT_ROOT / "compose.yaml").read_text()
    api_service = compose.split("\n  api:\n", maxsplit=1)[1].split("\n  web:\n", maxsplit=1)[0]

    assert (
        "DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-keeper}:"
        "${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}@db:5432/"
        "${POSTGRES_DB:-keeper}"
    ) in api_service
    assert "@localhost:5432" not in api_service


def test_compose_runs_healthchecked_loopback_only_clamav_with_persistent_definitions() -> None:
    compose = (PROJECT_ROOT / "compose.yaml").read_text()
    clamav_service = compose.split("\n  clamav:\n", maxsplit=1)[1].split("\n  api:\n", maxsplit=1)[
        0
    ]

    assert "image: clamav/clamav:stable" in clamav_service
    assert "127.0.0.1:3310:3310" in clamav_service
    assert "keeper_clamav:/var/lib/clamav" in clamav_service
    assert "/usr/local/bin/clamdcheck.sh" in clamav_service
    assert "start_period: 10m" in clamav_service
    assert "privileged:" not in clamav_service
    assert "/var/run/docker.sock" not in clamav_service
    assert "keeper_clamav:" in compose


def test_compose_api_waits_for_clamav_and_uses_internal_fail_closed_scanner() -> None:
    compose = (PROJECT_ROOT / "compose.yaml").read_text()
    api_service = compose.split("\n  api:\n", maxsplit=1)[1].split("\n  web:\n", maxsplit=1)[0]

    assert "MALWARE_SCANNER_BACKEND: clamav" in api_service
    assert 'MALWARE_SCANNER_FAIL_CLOSED: "true"' in api_service
    assert "CLAMAV_HOST: clamav" in api_service
    assert "CLAMAV_PORT: 3310" in api_service
    assert "CLAMAV_CONNECT_TIMEOUT_SECONDS: 2" in api_service
    assert "CLAMAV_READ_TIMEOUT_SECONDS: 15" in api_service
    assert "clamav:\n        condition: service_healthy" in api_service
    assert "MALWARE_SCANNER_BACKEND: disabled" not in api_service
