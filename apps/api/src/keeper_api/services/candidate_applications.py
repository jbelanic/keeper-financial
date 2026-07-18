from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keeper_api.models.domain import (
    Candidate,
    CandidateApplication,
    CandidateEducationEntry,
    CandidateEmploymentEntry,
    CandidateStatusHistory,
    RecruitmentPosting,
    Role,
    User,
    UserIdentity,
    UserRole,
)
from keeper_api.models.statuses import CandidateStatus
from keeper_api.schemas.candidate_applications import (
    ApplicationDraftUpdate,
    CandidateApplicationResponse,
    EducationEntryResponse,
    EmploymentEntryResponse,
)
from keeper_api.services.audit import AuditService
from keeper_api.services.auth import ExternalIdentity
from keeper_api.services.candidate_privacy import CANDIDATE_PRIVACY_DISCLOSURE


class CandidateApplicationConflict(ValueError):
    pass


class CandidateApplicationInvalid(ValueError):
    pass


NONTERMINAL_APPLICATION_STATUSES: tuple[str, ...] = tuple(
    status.value
    for status in CandidateStatus
    if status
    not in {
        CandidateStatus.PROSPECT,
        CandidateStatus.WITHDRAWN,
        CandidateStatus.DECLINED,
    }
)


def candidate_application_response(
    db: Session, application: CandidateApplication
) -> CandidateApplicationResponse:
    employment = db.scalars(
        select(CandidateEmploymentEntry)
        .where(CandidateEmploymentEntry.application_id == application.id)
        .order_by(CandidateEmploymentEntry.position)
    ).all()
    education = db.scalars(
        select(CandidateEducationEntry)
        .where(CandidateEducationEntry.application_id == application.id)
        .order_by(CandidateEducationEntry.position)
    ).all()
    data = {
        column: getattr(application, column)
        for column in CandidateApplicationResponse.model_fields
        if column not in {"employment", "education"}
    }
    data["employment"] = [
        EmploymentEntryResponse.model_validate(item, from_attributes=True) for item in employment
    ]
    data["education"] = [
        EducationEntryResponse.model_validate(item, from_attributes=True) for item in education
    ]
    return CandidateApplicationResponse.model_validate(data)


def provision_application(
    db: Session,
    *,
    identity: ExternalIdentity,
    posting_slug: str,
    request_id: str | None,
) -> tuple[CandidateApplication, bool]:
    if not identity.verified:
        raise PermissionError("verified provider identity is required")
    try:
        posting = db.scalar(
            select(RecruitmentPosting)
            .where(
                RecruitmentPosting.slug == posting_slug, RecruitmentPosting.status == "published"
            )
            .with_for_update()
        )
        if posting is None:
            raise LookupError("posting not found")
        linked = db.execute(
            select(User, UserIdentity)
            .join(UserIdentity, UserIdentity.user_id == User.id)
            .where(
                UserIdentity.provider == "supabase",
                UserIdentity.provider_subject == identity.subject,
            )
        ).one_or_none()
        audit = AuditService(db)
        if linked is not None:
            user, user_identity = linked
            if user.email.casefold() != identity.email.casefold():
                raise CandidateApplicationConflict("identity email conflicts with the linked user")
            if not user.is_active:
                raise PermissionError("active application access is required")
            user_identity.verified_at = user_identity.verified_at or datetime.now(UTC)
        else:
            existing_email = db.scalar(
                select(User).where(func.lower(User.email) == identity.email.casefold())
            )
            if existing_email is not None:
                raise CandidateApplicationConflict("email is already linked to another identity")
            user = User(email=identity.email, display_name="Candidate", is_active=True)
            db.add(user)
            db.flush()
            user_identity = UserIdentity(
                user_id=user.id,
                provider="supabase",
                provider_subject=identity.subject,
                verified_at=datetime.now(UTC),
            )
            db.add(user_identity)
            db.flush()
            audit.record(
                "user_identity.linked",
                "user_identity",
                user_identity.id,
                actor_user_id=user.id,
                request_id=request_id,
                safe_metadata={"provider": "supabase", "source": "candidate_application_start"},
            )
        role_codes = set(
            db.scalars(
                select(Role.code)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == user.id)
            ).all()
        )
        if role_codes - {"candidate"}:
            raise PermissionError("candidate self-provisioning is not available for this account")
        candidate_role = db.scalar(select(Role).where(Role.code == "candidate"))
        if candidate_role is None:
            candidate_role = Role(code="candidate", description="Candidate portal access")
            db.add(candidate_role)
            db.flush()
        if "candidate" not in role_codes:
            grant = UserRole(user_id=user.id, role_id=candidate_role.id, granted_by_user_id=None)
            db.add(grant)
            db.flush()
            audit.record(
                "role.granted",
                "user_role",
                grant.id,
                actor_user_id=user.id,
                request_id=request_id,
                safe_metadata={"role": "candidate", "source": "candidate_application_start"},
            )
        candidate = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
        if candidate is None:
            candidate = Candidate(user_id=user.id, status="application_started")
            db.add(candidate)
            db.flush()
        # Mirror the denied candidate-lifecycle enforcement that authorize_portal
        # applies to the candidate portal. The anonymous provisioning boundary must
        # not let a suspended/offboarding/offboarded candidate start applications
        # even when the account itself remains active (B1).
        elif CandidateStatus(candidate.status) in (
            CandidateStatus.SUSPENDED,
            CandidateStatus.OFFBOARDING,
            CandidateStatus.OFFBOARDED,
        ):
            raise PermissionError("candidate access is unavailable")
        existing = db.scalar(
            select(CandidateApplication).where(
                CandidateApplication.candidate_id == candidate.id,
                CandidateApplication.recruitment_posting_id == posting.id,
                CandidateApplication.status.in_(NONTERMINAL_APPLICATION_STATUSES),
            )
        )
        if existing is not None:
            db.commit()
            return existing, False
        attempt = (
            db.scalar(
                select(func.max(CandidateApplication.attempt_number)).where(
                    CandidateApplication.candidate_id == candidate.id,
                    CandidateApplication.recruitment_posting_id == posting.id,
                )
            )
            or 0
        ) + 1
        application = CandidateApplication(
            candidate_id=candidate.id,
            recruitment_posting_id=posting.id,
            attempt_number=attempt,
            source_posting_slug=posting.slug,
            source_posting_title=posting.title,
            source_posting_version=posting.version,
            schema_version="candidate-application-2026-07-15-v1",
            revision=1,
            state="draft",
            status="application_started",
            email=identity.email,
        )
        db.add(application)
        db.flush()
        audit.record(
            "candidate_application.started",
            "candidate_application",
            application.id,
            actor_user_id=user.id,
            request_id=request_id,
            safe_metadata={
                "status": "application_started",
                "source_posting_id": str(posting.id),
                "source_posting_version": posting.version,
            },
        )
        db.commit()
        db.refresh(application)
        return application, True
    except IntegrityError as exc:
        db.rollback()
        linked = db.execute(
            select(User, UserIdentity)
            .join(UserIdentity, UserIdentity.user_id == User.id)
            .where(
                UserIdentity.provider == "supabase",
                UserIdentity.provider_subject == identity.subject,
            )
        ).one_or_none()
        if linked is not None:
            user, _user_identity = linked
            candidate = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
            posting = db.scalar(
                select(RecruitmentPosting).where(
                    RecruitmentPosting.slug == posting_slug,
                    RecruitmentPosting.status == "published",
                )
            )
            if (
                candidate is not None
                and posting is not None
                and user.is_active
                and user.email.casefold() == identity.email.casefold()
            ):
                existing = db.scalar(
                    select(CandidateApplication).where(
                        CandidateApplication.candidate_id == candidate.id,
                        CandidateApplication.recruitment_posting_id == posting.id,
                        CandidateApplication.status.in_(NONTERMINAL_APPLICATION_STATUSES),
                    )
                )
                if existing is not None:
                    return existing, False
        raise CandidateApplicationConflict(
            "application start conflicted with another request"
        ) from exc
    except Exception:
        db.rollback()
        raise


def owned_application(
    db: Session, application_id: uuid.UUID, candidate_id: uuid.UUID, *, lock: bool = False
) -> CandidateApplication:
    statement = select(CandidateApplication).where(
        CandidateApplication.id == application_id,
        CandidateApplication.candidate_id == candidate_id,
    )
    if lock:
        statement = statement.with_for_update()
    application = db.scalar(statement)
    if application is None:
        raise LookupError("application not found")
    return application


def save_draft(
    db: Session,
    application: CandidateApplication,
    payload: ApplicationDraftUpdate,
) -> CandidateApplication:
    if application.state != "draft":
        raise CandidateApplicationConflict("submitted or withdrawn applications are read-only")
    if application.revision != payload.expected_revision:
        raise CandidateApplicationConflict("application revision has changed")
    values = payload.model_dump(exclude_unset=True)
    values.pop("expected_revision")
    employment = values.pop("employment", None)
    education = values.pop("education", None)
    merged_source = values.get("referral_source", application.referral_source)
    merged_detail = values.get("referral_detail", application.referral_detail)
    if merged_detail is not None and merged_source not in {"employee_or_agent_referral", "other"}:
        raise CandidateApplicationInvalid("referral detail is not allowed for this source")
    for field, value in values.items():
        setattr(application, field, value)
    if employment is not None:
        db.execute(
            delete(CandidateEmploymentEntry).where(
                CandidateEmploymentEntry.application_id == application.id
            )
        )
        for position, entry in enumerate(employment):
            db.add(
                CandidateEmploymentEntry(application_id=application.id, position=position, **entry)
            )
    if education is not None:
        db.execute(
            delete(CandidateEducationEntry).where(
                CandidateEducationEntry.application_id == application.id
            )
        )
        for position, entry in enumerate(education):
            db.add(
                CandidateEducationEntry(application_id=application.id, position=position, **entry)
            )
    application.revision += 1
    db.commit()
    db.refresh(application)
    return application


def submit_application(
    db: Session,
    application: CandidateApplication,
    *,
    expected_revision: int,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateApplication:
    if application.state == "submitted":
        return application
    if application.state != "draft":
        raise CandidateApplicationConflict("application cannot be submitted")
    if application.revision != expected_revision:
        raise CandidateApplicationConflict("application revision has changed")
    required = [
        application.given_name,
        application.family_name,
        application.email,
        application.phone,
        application.city,
        application.country_code,
        application.preferred_contact_method,
    ]
    if any(not value for value in required):
        raise CandidateApplicationInvalid("required contact information is incomplete")
    if not application.interest_statement or len(application.interest_statement) < 100:
        raise CandidateApplicationInvalid("interest statement must contain at least 100 characters")
    if not application.privacy_acknowledged or not application.information_accuracy_confirmed:
        raise CandidateApplicationInvalid("privacy and accuracy confirmations are required")
    now = datetime.now(UTC)
    application.state = "submitted"
    application.status = "application_submitted"
    application.submitted_at = now
    application.privacy_disclosure_version = CANDIDATE_PRIVACY_DISCLOSURE.version
    application.privacy_acknowledged_at = now
    application.revision += 1
    db.add(
        CandidateStatusHistory(
            candidate_id=application.candidate_id,
            application_id=application.id,
            previous_status="application_started",
            new_status="application_submitted",
            actor_user_id=actor_user_id,
            reason=None,
        )
    )
    AuditService(db).record(
        "candidate_application.submitted",
        "candidate_application",
        application.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={
            "previous_status": "application_started",
            "new_status": "application_submitted",
            "schema_version": application.schema_version,
            "disclosure_version": CANDIDATE_PRIVACY_DISCLOSURE.version,
        },
    )
    candidate = db.get(Candidate, application.candidate_id)
    if candidate is not None and candidate.status == "application_started":
        candidate.status = "application_submitted"
    db.commit()
    db.refresh(application)
    return application


def withdraw_application(
    db: Session,
    application: CandidateApplication,
    *,
    expected_revision: int,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateApplication:
    if application.state == "withdrawn":
        return application
    if application.state not in {"draft", "submitted"}:
        raise CandidateApplicationConflict("application cannot be withdrawn")
    if application.revision != expected_revision:
        raise CandidateApplicationConflict("application revision has changed")
    previous = application.status
    application.state = "withdrawn"
    application.status = "withdrawn"
    application.withdrawn_at = datetime.now(UTC)
    application.revision += 1
    db.add(
        CandidateStatusHistory(
            candidate_id=application.candidate_id,
            application_id=application.id,
            previous_status=previous,
            new_status="withdrawn",
            actor_user_id=actor_user_id,
            reason=None,
        )
    )
    AuditService(db).record(
        "candidate_application.withdrawn",
        "candidate_application",
        application.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"previous_status": previous, "new_status": "withdrawn"},
    )
    db.commit()
    db.refresh(application)
    return application
