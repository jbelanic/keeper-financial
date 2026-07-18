from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from urllib.error import URLError
from urllib.request import Request

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
from keeper_api.models.domain import (
    Candidate,
    CandidateApplication,
    RecruitmentPosting,
    Role,
    User,
    UserIdentity,
    UserRole,
)
from keeper_api.services import auth

JWT_SUBJECT = "11111111-2222-4333-8444-555555555555"
JWT_EMAIL = "synthetic-jwt@example.test"


def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="local",
        dev_auth_enabled=False,
        supabase_issuer="http://127.0.0.1:54321/auth/v1",
        supabase_audience="authenticated",
        supabase_jwks_url="http://127.0.0.1:54321/auth/v1/.well-known/jwks.json",
        supabase_user_url="http://127.0.0.1:54321/auth/v1/user",
        supabase_anon_key="synthetic-anon-key",
        supabase_jwt_algorithms="ES256",
    )


def token(
    private_key: ec.EllipticCurvePrivateKey,
    *,
    issuer: str = "http://127.0.0.1:54321/auth/v1",
    audience: str = "authenticated",
    expires_delta: timedelta = timedelta(minutes=5),
    subject: str = JWT_SUBJECT,
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "email": JWT_EMAIL,
            "user_metadata": {"email_verified": True},
            "aal": "aal2",
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + expires_delta,
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "synthetic-key"},
    )


def use_key(monkeypatch: pytest.MonkeyPatch, key: ec.EllipticCurvePublicKey) -> None:
    monkeypatch.setattr(
        auth.PyJWKClient,
        "get_signing_key_from_jwt",
        lambda _self, _token: SimpleNamespace(key=key),
    )


def use_provider_user(
    monkeypatch: pytest.MonkeyPatch,
    *,
    subject: str = JWT_SUBJECT,
    email: str = JWT_EMAIL,
    confirmed: bool = True,
) -> None:
    payload = json.dumps(
        {
            "id": subject,
            "email": email,
            "email_confirmed_at": "2026-07-18T01:00:00Z" if confirmed else None,
        }
    ).encode()

    class ProviderResponse:
        def __enter__(self) -> ProviderResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, limit: int) -> bytes:
            assert limit == auth._MAX_PROVIDER_USER_BYTES + 1
            return payload

    def provider_user(request: Request, timeout: float) -> ProviderResponse:
        assert request.full_url == "http://127.0.0.1:54321/auth/v1/user"
        assert timeout == 5
        return ProviderResponse()

    monkeypatch.setattr(auth, "urlopen", provider_user)


def test_es256_token_enforces_signature_issuer_audience_and_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    use_key(monkeypatch, private_key.public_key())
    claims = auth._decode_token(token(private_key), settings())
    assert claims["sub"] == JWT_SUBJECT
    assert "email_verified" not in claims
    assert claims["user_metadata"]["email_verified"] is True
    assert claims["aal"] == "aal2"

    for invalid in (
        token(private_key, issuer="http://invalid.example.test/auth/v1"),
        token(private_key, audience="wrong-audience"),
        token(private_key, expires_delta=timedelta(seconds=-1)),
    ):
        with pytest.raises(HTTPException) as exc:
            auth._decode_token(invalid, settings())
        assert exc.value.status_code == 401


def test_es256_token_rejects_key_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    signing_key = ec.generate_private_key(ec.SECP256R1())
    wrong_key = ec.generate_private_key(ec.SECP256R1())
    use_key(monkeypatch, wrong_key.public_key())
    with pytest.raises(HTTPException) as exc:
        auth._decode_token(token(signing_key), settings())
    assert exc.value.status_code == 401


def test_confirmed_supabase_user_verification_does_not_trust_user_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    use_key(monkeypatch, private_key.public_key())
    use_provider_user(monkeypatch)
    access_token = token(private_key)
    claims = auth._decode_token(access_token, settings())

    identity = auth._verified_provider_identity(access_token, claims, settings())

    assert identity == auth.ExternalIdentity(
        subject=JWT_SUBJECT,
        email=JWT_EMAIL,
        verified=True,
        aal="aal2",
    )


def test_unconfirmed_or_invalid_subject_is_denied_without_local_provisioning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    use_key(monkeypatch, private_key.public_key())
    use_provider_user(monkeypatch, confirmed=False)
    access_token = token(private_key)
    with pytest.raises(HTTPException) as unconfirmed:
        auth._verified_provider_identity(
            access_token,
            auth._decode_token(access_token, settings()),
            settings(),
        )
    assert unconfirmed.value.status_code == 403

    invalid_subject_token = token(private_key, subject="not-a-uuid")
    with pytest.raises(HTTPException) as invalid_subject:
        auth._verified_provider_identity(
            invalid_subject_token,
            auth._decode_token(invalid_subject_token, settings()),
            settings(),
        )
    assert invalid_subject.value.status_code == 401


def test_authoritative_provider_verification_fails_closed_with_bounded_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    use_key(monkeypatch, private_key.public_key())
    access_token = token(private_key)
    verification_settings = settings()
    claims = auth._decode_token(access_token, verification_settings)

    verification_settings.supabase_anon_key = None
    with pytest.raises(HTTPException) as missing_configuration:
        auth._verified_provider_identity(access_token, claims, verification_settings)
    assert missing_configuration.value.status_code == 503
    assert missing_configuration.value.detail == "identity verification is unavailable"

    verification_settings.supabase_anon_key = SecretStr("synthetic-anon-key")
    monkeypatch.setattr(
        auth,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("synthetic unavailable")),
    )
    with pytest.raises(HTTPException) as unavailable:
        auth._verified_provider_identity(access_token, claims, verification_settings)
    assert unavailable.value.status_code == 503
    assert unavailable.value.detail == "identity verification is unavailable"


def test_verified_unmapped_jwt_provisions_idempotently_and_then_resolves_candidate_access(
    client: TestClient,
    db: Session,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings.dev_auth_enabled = False
    settings.supabase_anon_key = SecretStr("synthetic-anon-key")
    private_key = ec.generate_private_key(ec.SECP256R1())
    use_key(monkeypatch, private_key.public_key())
    use_provider_user(monkeypatch)
    for slug in ("jwt-posting-one", "jwt-posting-two"):
        db.add(
            RecruitmentPosting(
                slug=slug,
                title=f"Synthetic {slug}",
                summary="Synthetic verified JWT provisioning fixture.",
                body="Not a real posting.",
                status="published",
                version=1,
                published_at=datetime.now(UTC),
            )
        )
    db.commit()
    access_token = token(private_key)
    headers = {"Authorization": f"Bearer {access_token}"}

    assert client.get("/api/v1/auth/access?area=candidate", headers=headers).status_code == 403
    first = client.post(
        "/api/v1/recruitment/postings/jwt-posting-one/applications/start", headers=headers
    )
    retry = client.post(
        "/api/v1/recruitment/postings/jwt-posting-one/applications/start", headers=headers
    )
    second_posting = client.post(
        "/api/v1/recruitment/postings/jwt-posting-two/applications/start", headers=headers
    )

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.json()["id"] == first.json()["id"]
    assert second_posting.status_code == 201
    assert second_posting.json()["id"] != first.json()["id"]
    assert client.get("/api/v1/auth/access?area=candidate", headers=headers).status_code == 200
    user = db.query(User).filter_by(email=JWT_EMAIL).one()
    assert db.query(UserIdentity).filter_by(user_id=user.id).count() == 1
    assert db.query(Candidate).filter_by(user_id=user.id).count() == 1
    assert db.query(CandidateApplication).count() == 2
    roles = {
        role.code
        for role in db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
    }
    assert roles == {"candidate"}


@pytest.mark.skipif(
    not os.getenv("KEEPER_LOCAL_SUPABASE_ACCESS_TOKEN")
    or not os.getenv("KEEPER_LOCAL_SUPABASE_ANON_KEY"),
    reason="local access token and anon key enable genuine Supabase verification",
)
def test_genuine_local_supabase_token_against_live_jwks() -> None:
    # The token is read only from the operator's process environment and is
    # never printed, persisted, placed in a URL, or included in assertion text.
    access_token = os.environ["KEEPER_LOCAL_SUPABASE_ACCESS_TOKEN"]
    live_settings = settings()
    live_settings.supabase_anon_key = SecretStr(os.environ["KEEPER_LOCAL_SUPABASE_ANON_KEY"])
    claims = auth._decode_token(access_token, live_settings)
    identity = auth._verified_provider_identity(access_token, claims, live_settings)
    assert identity.verified is True
    assert identity.aal in {"aal1", "aal2"}
