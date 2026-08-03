from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
NGINX_CONFIG = PROJECT_ROOT / "infrastructure" / "nginx" / "keeper-financial.conf"


def test_nginx_ingress_uses_exact_public_hosts_and_loopback_upstreams() -> None:
    config = NGINX_CONFIG.read_text()

    assert "server_name keeperfinancial.ca;" in config
    assert "server_name www.keeperfinancial.ca;" in config
    assert "server_name apply.keeperfinancial.ca;" in config
    assert "server_name _;" not in config
    assert "proxy_pass http://127.0.0.1:3000;" in config
    assert "proxy_pass http://127.0.0.1:8000;" in config
    assert "proxy_pass http://api:8000" not in config


def test_nginx_api_proxy_preserves_fastapi_api_prefix_and_forwards_https_host() -> None:
    config = NGINX_CONFIG.read_text()
    api_location = config.split("    location /api/ {", maxsplit=1)[1].split("\n    }", maxsplit=1)[
        0
    ]

    assert "proxy_pass http://127.0.0.1:8000;" in api_location
    assert "proxy_pass http://127.0.0.1:8000/;" not in api_location
    assert "proxy_set_header Host $host;" in api_location
    assert "proxy_set_header X-Forwarded-Host $host;" in api_location
    assert "proxy_set_header X-Forwarded-Proto https;" in api_location
    assert "client_max_body_size 26m;" in config
    assert "proxy_read_timeout 300s;" in api_location


def test_nginx_ingress_does_not_expose_internal_keeper_or_operator_services() -> None:
    config = NGINX_CONFIG.read_text()

    for forbidden in ("5432", "9000", "9001", "3310", "54321", "54323", "54324"):
        assert f"127.0.0.1:{forbidden}" not in config
    assert "location /auth/" not in config
    assert "location /studio/" not in config
    assert "location /minio/" not in config
