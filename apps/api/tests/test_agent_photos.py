from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from conftest import create_user
from document_samples import valid_image, valid_pdf
from keeper_api.core.config import Settings
from keeper_api.models.domain import AuditEvent
from keeper_api.services.agent_photos import photo_url
from keeper_api.services.storage import PUBLIC_IMAGE_PREFIX

PHOTO_URL = re.compile(r"^https://keeperfinancial\.ca/api/v1/agent-photos/[0-9a-f]{32}\.jpg$")
ADMIN_HEADERS = {
    "Authorization": "Bearer local-dev-test-token",
    "X-Dev-Auth-Sub": "photo-admin",
    "X-Dev-Auth-AAL": "aal2",
}


def _admin(db: Session):
    user, _ = create_user(db, subject="photo-admin", role_code="brokerage_admin")
    return user


def _upload(
    client: TestClient,
    *,
    filename: str = "headshot.jpg",
    content_type: str = "image/jpeg",
    content: bytes | None = None,
):
    return client.post(
        "/api/v1/admin/agent-photos",
        files={
            "file": (
                filename,
                valid_image("JPEG") if content is None else content,
                content_type,
            )
        },
        headers=ADMIN_HEADERS,
    )


def _photo_path(photo_url: str) -> str:
    return photo_url.removeprefix("https://keeperfinancial.ca")


def test_admin_upload_returns_stable_url_and_public_read_serves_the_bytes(
    client: TestClient, db: Session, settings: Settings
) -> None:
    _admin(db)

    response = _upload(client, content=valid_image("JPEG"))

    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "private, no-store"
    photo_url = response.json()["photo_url"]
    assert PHOTO_URL.fullmatch(photo_url), photo_url

    stored = sorted((settings.local_storage_path / PUBLIC_IMAGE_PREFIX).iterdir())
    assert len(stored) == 1
    assert stored[0].name == photo_url.rsplit("/", 1)[1]

    served = client.get(_photo_path(photo_url))
    assert served.status_code == 200
    assert served.content == valid_image("JPEG")
    assert served.headers["content-type"] == "image/jpeg"
    assert served.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert served.headers["x-content-type-options"] == "nosniff"


def test_upload_records_audit_evidence(client: TestClient, db: Session) -> None:
    _admin(db)

    photo_url = _upload(client).json()["photo_url"]

    event = db.scalar(select(AuditEvent).where(AuditEvent.event_type == "agent_photo.stored"))
    assert event is not None
    assert event.target_type == "agent_photo"
    assert str(event.target_id).replace("-", "") == photo_url.rsplit("/", 1)[1].split(".", 1)[0]
    assert event.safe_metadata == {
        "content_type": "image/jpeg",
        "size_bytes": len(valid_image("JPEG")),
    }


def test_upload_requires_authentication_and_administrator_authority(
    client: TestClient, db: Session, settings: Settings
) -> None:
    _admin(db)
    files = {"file": ("headshot.jpg", valid_image("JPEG"), "image/jpeg")}

    anonymous = client.post("/api/v1/admin/agent-photos", files=files)
    assert anonymous.status_code == 401
    assert anonymous.headers["Cache-Control"] == "private, no-store"

    create_user(db, subject="photo-agent", role_code="agent", candidate_status="active")
    not_admin = client.post(
        "/api/v1/admin/agent-photos",
        files={"file": ("headshot.jpg", valid_image("JPEG"), "image/jpeg")},
        headers={
            "Authorization": "Bearer local-dev-test-token",
            "X-Dev-Auth-Sub": "photo-agent",
            "X-Dev-Auth-AAL": "aal2",
        },
    )
    assert not_admin.status_code == 403

    assert not (settings.local_storage_path / PUBLIC_IMAGE_PREFIX).exists()


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "code"),
    [
        ("headshot.pdf", "application/pdf", valid_pdf(), 415),
        ("headshot.jpg", "image/jpeg", valid_pdf(), 415),
        ("headshot.gif", "image/gif", valid_image("PNG"), 415),
        ("headshot.jpg", "image/jpeg", b"\xff\xd8\xffnot-an-image", 422),
        ("headshot.png", "image/png", b"", 422),
    ],
)
def test_upload_rejects_unsupported_or_malformed_media(
    client: TestClient,
    db: Session,
    filename: str,
    content_type: str,
    content: bytes,
    code: int,
) -> None:
    _admin(db)

    response = _upload(client, filename=filename, content_type=content_type, content=content)

    assert response.status_code == code, response.text
    assert response.headers["cache-control"] == "private, no-store"


def test_upload_fails_closed_when_the_scanner_is_unavailable(
    client: TestClient, db: Session, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    _admin(db)
    monkeypatch.setattr(settings, "malware_scanner_backend", "disabled")

    response = _upload(client)

    assert response.status_code == 503
    assert response.json()["detail"] == "photo scanning is unavailable"
    assert not (settings.local_storage_path / PUBLIC_IMAGE_PREFIX).exists()


def test_public_read_refuses_anything_that_is_not_a_generated_photo(
    client: TestClient, db: Session, settings: Settings
) -> None:
    _admin(db)
    private_dir = settings.local_storage_path / "candidate"
    private_dir.mkdir(parents=True, exist_ok=True)
    (private_dir / "0123456789abcdef0123456789abcdef").write_bytes(b"%PDF-1.4 private")

    for photo_id in (
        "not-a-photo",
        "0123456789abcdef0123456789abcdef",
        "0123456789abcdef0123456789abcdef.exe",
        "0123456789abcdef0123456789abcdef.jpg",
    ):
        response = client.get(f"/api/v1/agent-photos/{photo_id}")
        assert response.status_code == 404, photo_id
        assert response.json() == {"detail": "agent photo was not found"}

    # A traversal-shaped identifier never reaches an object and never leaks one.
    for traversal in ("..%2F..%2Fsecret.jpg", "%2E%2E%2F%2E%2E%2Fsecret.jpg"):
        response = client.get(f"/api/v1/agent-photos/{traversal}")
        assert response.status_code == 404, traversal


def test_replacing_a_photo_deletes_the_previous_object(
    client: TestClient, db: Session, settings: Settings
) -> None:
    _admin(db)
    agent, _ = create_user(db, subject="photo-owner", role_code="agent", candidate_status="active")
    first_url = _upload(client).json()["photo_url"]

    created = client.post(
        "/api/v1/admin/agent-profiles",
        json={
            "user_id": str(agent.id),
            "slug": "photo-owner",
            "licensed_name": "Photo Owner",
            "approved_title": "Mortgage Agent",
            "licence_number": "M00000001",
            "biography": "Synthetic biography.",
            "photo_url": first_url,
            "photo_alt_text": "Photo Owner",
        },
        headers=ADMIN_HEADERS,
    )
    assert created.status_code == 201, created.text

    second_url = _upload(client).json()["photo_url"]
    updated = client.patch(
        f"/api/v1/admin/agent-profiles/{created.json()['id']}",
        json={"photo_url": second_url},
        headers=ADMIN_HEADERS,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["photo_url"] == second_url

    assert client.get(_photo_path(first_url)).status_code == 404
    assert client.get(_photo_path(second_url)).status_code == 200
    assert len(list((settings.local_storage_path / PUBLIC_IMAGE_PREFIX).iterdir())) == 1


def test_clearing_a_photo_deletes_the_keeper_managed_object(
    client: TestClient, db: Session, settings: Settings
) -> None:
    _admin(db)
    agent, _ = create_user(db, subject="photo-clear", role_code="agent", candidate_status="active")
    photo_url = _upload(client).json()["photo_url"]
    created = client.post(
        "/api/v1/admin/agent-profiles",
        json={
            "user_id": str(agent.id),
            "slug": "photo-clear",
            "licensed_name": "Photo Clear",
            "approved_title": "Mortgage Agent",
            "licence_number": "M00000002",
            "biography": "Synthetic biography.",
            "photo_url": photo_url,
            "photo_alt_text": "Photo Clear",
        },
        headers=ADMIN_HEADERS,
    )
    assert created.status_code == 201, created.text

    cleared = client.patch(
        f"/api/v1/admin/agent-profiles/{created.json()['id']}",
        json={"photo_url": None, "photo_alt_text": None},
        headers=ADMIN_HEADERS,
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["photo_url"] is None
    assert client.get(_photo_path(photo_url)).status_code == 404


def test_external_photo_urls_are_left_alone(
    client: TestClient, db: Session, settings: Settings
) -> None:
    _admin(db)
    agent, _ = create_user(
        db, subject="photo-external", role_code="agent", candidate_status="active"
    )
    created = client.post(
        "/api/v1/admin/agent-profiles",
        json={
            "user_id": str(agent.id),
            "slug": "photo-external",
            "licensed_name": "Photo External",
            "approved_title": "Mortgage Agent",
            "licence_number": "M00000003",
            "biography": "Synthetic biography.",
            "photo_url": "https://media.example.test/agents/photo-external.jpg",
            "photo_alt_text": "Photo External",
        },
        headers=ADMIN_HEADERS,
    )
    assert created.status_code == 201, created.text

    replaced = client.patch(
        f"/api/v1/admin/agent-profiles/{created.json()['id']}",
        json={"photo_url": None, "photo_alt_text": None},
        headers=ADMIN_HEADERS,
    )
    assert replaced.status_code == 200, replaced.text
    # An externally hosted URL is never deleted by Keeper; only its reference is dropped.
    assert replaced.json()["photo_url"] is None


# --- PUBLIC_SITE_BASE_URL shapes (decision 56 amendment, 2026-10-25) ---------
# The uploaded photo's stable URL is composed from this origin, so the value has to
# describe the environment the photo is served from. Production stays HTTPS-only;
# dev/test may point at the loopback origin that actually serves the route.

PHOTO_ID = "0123456789abcdef0123456789abcdef.jpg"


def _settings(**overrides: object) -> Settings:
    # `_env_file=None` keeps the check independent of the host's real `.env`.
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


def test_photo_url_uses_the_configured_origin() -> None:
    for base, prefix in (
        ("https://keeperfinancial.ca", "https://keeperfinancial.ca"),
        ("http://localhost:3000", "http://localhost:3000"),
        ("http://127.0.0.1:8000", "http://127.0.0.1:8000"),
    ):
        settings = _settings(public_site_base_url=base)

        assert photo_url(settings, PHOTO_ID) == f"{prefix}/api/v1/agent-photos/{PHOTO_ID}"


@pytest.mark.parametrize(
    "base",
    [
        "http://example.com",  # http outside loopback
        "http://localhost",  # loopback without an explicit port
        "http://localhost:3000/nested",  # path
        "http://localhost:3000?x=1",  # query
        "https://keeperfinancial.ca:8443",  # non-443 port
        "https://keeperfinancial.ca/photo",  # path on the https shape
    ],
)
def test_photo_origin_rejects_unsafe_shapes_outside_production(base: str) -> None:
    with pytest.raises(ValidationError) as raised:
        _settings(public_site_base_url=base)

    assert "PUBLIC_SITE_BASE_URL" in str(raised.value)


def test_production_rejects_a_loopback_photo_origin() -> None:
    with pytest.raises(ValidationError) as raised:
        _settings(app_env="production", public_site_base_url="http://localhost:3000")

    assert "PUBLIC_SITE_BASE_URL" in str(raised.value)
