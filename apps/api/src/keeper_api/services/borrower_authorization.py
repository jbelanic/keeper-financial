from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
)
from keeper_api.models.domain import Candidate, Role, User, UserRole
from keeper_api.models.statuses import CandidateStatus
from keeper_api.services.auth import Principal
from keeper_api.services.borrower_crypto import (
    BorrowerCryptoState,
    verify_capability_digest,
)


@dataclass(frozen=True)
class BorrowerCapabilityContext:
    application_id: uuid.UUID
    capability_session_id: uuid.UUID
    revision: int
    lifecycle_status: BorrowerApplicationLifecycleStatus


def validate_borrower_origin(request: Request, settings: Settings) -> None:
    host = request.headers.get("host", "")
    origin = request.headers.get("origin", "")

    expected_host = "apply.keeperfinancial.ca"
    expected_origin = "https://apply.keeperfinancial.ca"

    if settings.app_env == "local":
        expected_host = "localhost:8000"
        expected_origin = "http://localhost:8000"

    if host.split(":")[0] != expected_host.split(":")[0]:
        raise HTTPException(status_code=403, detail="forbidden")

    if request.method in ("POST", "PATCH", "PUT", "DELETE"):
        if origin and origin != expected_origin:
            raise HTTPException(status_code=403, detail="forbidden")

        csrf_header = request.headers.get("x-keeper-borrower-csrf")
        if csrf_header != "1":
            raise HTTPException(status_code=403, detail="forbidden")


def require_borrower_feature_enabled(settings: Settings) -> None:
    if not settings.borrower_application_enabled:
        raise HTTPException(status_code=503, detail="borrower application is unavailable")


def extract_capability_from_cookie(request: Request) -> str | None:
    cookie_header = request.headers.get("cookie", "")
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("__Host-keeper-borrower-draft="):
            return part[len("__Host-keeper-borrower-draft=") :]
    return None


def verify_borrower_capability(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
    capability: str,
) -> BorrowerCapabilityContext:
    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="application not found")

    if application.lifecycle_status != BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise HTTPException(status_code=404, detail="application not found")

    if application.capability_digest is None:
        raise HTTPException(status_code=404, detail="application not found")

    if application.capability_revoked_at is not None:
        raise HTTPException(status_code=404, detail="application not found")

    if crypto_state is None:
        raise HTTPException(status_code=503, detail="borrower cryptography is unavailable")

    if not verify_capability_digest(
        capability, application.capability_digest, crypto_state.hmac_key
    ):
        raise HTTPException(status_code=404, detail="application not found")

    return BorrowerCapabilityContext(
        application_id=application.id,
        capability_session_id=application.capability_session_id,
        revision=application.revision,
        lifecycle_status=BorrowerApplicationLifecycleStatus(application.lifecycle_status),
    )


def require_internal_agent_access(
    principal: Principal,
    application_id: uuid.UUID,
    db: Session,
    settings: Settings,
) -> Principal:
    if not principal.is_active or principal.verified_at is None:
        raise HTTPException(status_code=403, detail="active verified access is required")

    if principal.aal != "aal2":
        raise HTTPException(
            status_code=403, detail="MFA is required for borrower application access"
        )

    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="application not found")

    if application.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise HTTPException(status_code=404, detail="application not found")

    from keeper_api.services.borrower_applications import has_submission_evidence

    if not has_submission_evidence(db, application_id):
        raise HTTPException(status_code=404, detail="application not found")

    if "agent" not in principal.roles:
        raise HTTPException(status_code=403, detail="agent access is required")

    candidate = db.scalar(select(Candidate).where(Candidate.user_id == principal.user_id))
    if candidate is None:
        raise HTTPException(status_code=403, detail="agent access is required")

    if candidate.status not in (CandidateStatus.ACTIVE,):
        raise HTTPException(status_code=403, detail="agent access is unavailable")

    if application.assigned_agent_id != principal.user_id:
        raise HTTPException(status_code=404, detail="application not found")

    return principal


def require_admin_borrower_access(
    principal: Principal,
    application_id: uuid.UUID,
    db: Session,
    settings: Settings,
) -> Principal:
    if not principal.is_active or principal.verified_at is None:
        raise HTTPException(status_code=403, detail="active verified access is required")

    if "brokerage_admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="brokerage administrator access is required")

    if settings.require_admin_mfa and principal.aal != "aal2":
        raise HTTPException(status_code=403, detail="administrator MFA is required")

    if principal.aal != "aal2":
        raise HTTPException(
            status_code=403, detail="MFA is required for borrower application access"
        )

    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="application not found")

    if application.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise HTTPException(status_code=404, detail="application not found")

    from keeper_api.services.borrower_applications import has_submission_evidence

    if not has_submission_evidence(db, application_id):
        raise HTTPException(status_code=404, detail="application not found")

    return principal


def require_admin_aal2_borrower_access(
    principal: Principal,
    application_id: uuid.UUID,
    db: Session,
    settings: Settings,
) -> Principal:
    if not principal.is_active or principal.verified_at is None:
        raise HTTPException(status_code=403, detail="active verified access is required")

    if "brokerage_admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="brokerage administrator access is required")

    if principal.aal != "aal2":
        raise HTTPException(status_code=403, detail="administrator MFA is required")

    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="application not found")

    if application.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise HTTPException(status_code=404, detail="application not found")

    from keeper_api.services.borrower_applications import has_submission_evidence

    if not has_submission_evidence(db, application_id):
        raise HTTPException(status_code=404, detail="application not found")

    return principal


def authorize_internal_borrower_reviewer(
    principal: Principal,
    application_id: uuid.UUID,
    db: Session,
    settings: Settings,
) -> tuple[Principal, str]:
    if "brokerage_admin" in principal.roles:
        return (
            require_admin_aal2_borrower_access(principal, application_id, db, settings),
            "brokerage_admin",
        )
    return (
        require_internal_agent_access(principal, application_id, db, settings),
        "agent",
    )


def resolve_agent_from_slug(
    db: Session,
    slug: str,
) -> uuid.UUID | None:
    from keeper_api.models.domain import AgentProfile

    profile = db.scalar(
        select(AgentProfile).where(
            AgentProfile.slug == slug,
            AgentProfile.status == "published",
        )
    )
    if profile is None:
        return None

    user = db.get(User, profile.user_id)
    if user is None or not user.is_active:
        return None

    has_agent_role = db.scalar(
        select(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id, Role.code == "agent")
    )
    if has_agent_role is None:
        return None

    candidate = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
    if candidate is None:
        return None

    if candidate.status != CandidateStatus.ACTIVE.value:
        return None

    return user.id


def validate_assignment_target(
    db: Session,
    agent_user_id: uuid.UUID,
) -> None:
    user = db.get(User, agent_user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=422, detail="invalid assignment target")

    has_agent_role = db.scalar(
        select(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id, Role.code == "agent")
    )
    if has_agent_role is None:
        raise HTTPException(status_code=422, detail="invalid assignment target")

    candidate = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
    if candidate is None:
        raise HTTPException(status_code=422, detail="invalid assignment target")

    if candidate.status != CandidateStatus.ACTIVE.value:
        raise HTTPException(status_code=422, detail="invalid assignment target")
