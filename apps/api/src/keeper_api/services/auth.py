from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.domain import Candidate, Role, User, UserIdentity, UserRole
from keeper_api.models.statuses import CandidateStatus

PortalArea = Literal["candidate", "admin", "agent"]
security = HTTPBearer(auto_error=False)
_PROVIDER_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_MAX_PROVIDER_USER_BYTES = 64 * 1024


def _provider_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 254 or not _PROVIDER_EMAIL.fullmatch(email):
        raise HTTPException(status_code=403, detail="verified provider email is invalid")
    return email


def _provider_subject(value: object) -> str:
    if not isinstance(value, str):
        raise HTTPException(status_code=401, detail="invalid identity token")
    try:
        return str(uuid.UUID(value))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid identity token") from exc


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    identity_subject: str
    verified_at: datetime | None
    roles: frozenset[str]
    is_active: bool
    aal: str
    candidate_id: uuid.UUID | None
    candidate_status: CandidateStatus | None


@dataclass(frozen=True)
class ExternalIdentity:
    subject: str
    email: str
    verified: bool
    aal: str


def _decode_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        signing_key = PyJWKClient(settings.supabase_jwks_url).get_signing_key_from_jwt(token).key
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key,
            algorithms=settings.jwt_algorithm_list,
            audience=settings.supabase_audience,
            issuer=settings.supabase_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
        return claims
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid identity token"
        ) from exc


def _verified_provider_identity(
    token: str, claims: dict[str, Any], settings: Settings
) -> ExternalIdentity:
    subject = _provider_subject(claims.get("sub"))
    claimed_email = claims.get("email")
    if not isinstance(claimed_email, str):
        raise HTTPException(status_code=401, detail="invalid identity token")
    email = _provider_email(claimed_email)
    if settings.supabase_anon_key is None:
        raise HTTPException(status_code=503, detail="identity verification is unavailable")
    request = Request(  # noqa: S310 -- production restricts this URL to local Supabase.
        settings.supabase_user_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "apikey": settings.supabase_anon_key.get_secret_value(),
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=settings.supabase_user_timeout_seconds) as provider_response:  # noqa: S310 -- URL is restricted above.
            payload_bytes = provider_response.read(_MAX_PROVIDER_USER_BYTES + 1)
    except HTTPError as exc:
        if exc.code in {401, 403}:
            raise HTTPException(status_code=401, detail="invalid identity token") from None
        raise HTTPException(
            status_code=503, detail="identity verification is unavailable"
        ) from None
    except (TimeoutError, URLError):
        raise HTTPException(
            status_code=503, detail="identity verification is unavailable"
        ) from None
    if len(payload_bytes) > _MAX_PROVIDER_USER_BYTES:
        raise HTTPException(status_code=503, detail="identity verification is unavailable")
    try:
        provider_user = json.loads(payload_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=503, detail="identity verification is unavailable"
        ) from None
    if not isinstance(provider_user, dict):
        raise HTTPException(status_code=503, detail="identity verification is unavailable")
    if provider_user.get("id") != subject:
        raise HTTPException(status_code=401, detail="invalid identity token")
    provider_email = provider_user.get("email")
    if not isinstance(provider_email, str) or _provider_email(provider_email) != email:
        raise HTTPException(status_code=401, detail="invalid identity token")
    confirmed_at = provider_user.get("email_confirmed_at")
    if not isinstance(confirmed_at, str) or not confirmed_at.strip():
        raise HTTPException(status_code=403, detail="verified provider identity is required")
    return ExternalIdentity(
        subject=subject,
        email=email,
        verified=True,
        aal=str(claims.get("aal", "aal1")),
    )


def _load_principal(db: Session, subject: str, aal: str) -> Principal:
    row = db.execute(
        select(User, UserIdentity)
        .join(UserIdentity, UserIdentity.user_id == User.id)
        .where(UserIdentity.provider == "supabase", UserIdentity.provider_subject == subject)
    ).one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="local application access is required"
        )
    user, identity = row
    roles = frozenset(
        db.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
        ).all()
    )
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
    return Principal(
        user_id=user.id,
        identity_subject=subject,
        verified_at=identity.verified_at,
        roles=roles,
        is_active=user.is_active,
        aal=aal,
        candidate_id=candidate.id if candidate else None,
        candidate_status=CandidateStatus(candidate.status) if candidate else None,
    )


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_dev_auth_sub: str | None = Header(default=None),
    x_dev_auth_aal: str = Header(default="aal1"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if settings.dev_auth_enabled and settings.app_env == "local" and x_dev_auth_sub:
        return _load_principal(db, x_dev_auth_sub, x_dev_auth_aal)
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        )
    claims = _decode_token(credentials.credentials, settings)
    subject = _provider_subject(claims.get("sub"))
    aal = claims.get("aal", "aal1")
    return _load_principal(db, subject, str(aal))


def get_verified_external_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_dev_auth_sub: str | None = Header(default=None),
    x_dev_auth_email: str | None = Header(default=None),
    x_dev_auth_verified: str = Header(default="false"),
    x_dev_auth_aal: str = Header(default="aal1"),
    settings: Settings = Depends(get_settings),
) -> ExternalIdentity:
    if settings.dev_auth_enabled and settings.app_env == "local" and x_dev_auth_sub:
        if not x_dev_auth_email:
            raise HTTPException(status_code=403, detail="verified provider email is required")
        return ExternalIdentity(
            subject=x_dev_auth_sub,
            email=_provider_email(x_dev_auth_email),
            verified=x_dev_auth_verified.lower() == "true",
            aal=x_dev_auth_aal,
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="authentication required")
    claims = _decode_token(credentials.credentials, settings)
    return _verified_provider_identity(credentials.credentials, claims, settings)


def authorize_portal(principal: Principal, area: PortalArea, settings: Settings) -> Principal:
    if not principal.is_active or principal.verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="active verified access is required"
        )
    if area == "candidate":
        if "candidate" not in principal.roles or principal.candidate_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="candidate access is required"
            )
        denied = {
            CandidateStatus.SUSPENDED,
            CandidateStatus.OFFBOARDING,
            CandidateStatus.OFFBOARDED,
        }
        if principal.candidate_status in denied:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="candidate access is unavailable"
            )
    elif area == "agent":
        if "agent" not in principal.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="agent access is required"
            )
        if principal.aal != "aal2":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="agent MFA is required"
            )
    else:
        if "brokerage_admin" not in principal.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="brokerage administrator access is required",
            )
        if settings.require_admin_mfa and principal.aal != "aal2":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="administrator MFA is required"
            )
    return principal


def require_candidate(
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Principal:
    return authorize_portal(principal, "candidate", settings)


def require_candidate_aal2(
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Principal:
    authorize_portal(principal, "candidate", settings)
    if principal.aal != "aal2":
        raise HTTPException(status_code=403, detail="candidate MFA is required for documents")
    return principal


def require_admin(
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Principal:
    return authorize_portal(principal, "admin", settings)


def require_admin_aal2(
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Principal:
    authorize_portal(principal, "admin", settings)
    if principal.aal != "aal2":
        raise HTTPException(status_code=403, detail="administrator MFA is required")
    return principal
