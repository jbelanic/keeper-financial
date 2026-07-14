from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

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

PortalArea = Literal["candidate", "admin"]
security = HTTPBearer(auto_error=False)


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
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid identity token"
        )
    aal = claims.get("aal", "aal1")
    return _load_principal(db, subject, str(aal))


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


def require_admin(
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Principal:
    return authorize_portal(principal, "admin", settings)
