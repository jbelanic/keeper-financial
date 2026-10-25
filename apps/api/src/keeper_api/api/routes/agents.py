from __future__ import annotations

import re
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.domain import AgentProfile, AgentReferralLink
from keeper_api.models.statuses import CandidateStatus
from keeper_api.schemas.agents import (
    AdminAgentProfile,
    AdminAgentProfileList,
    AgentPhotoUpload,
    AgentProfileCreate,
    AgentProfileUpdate,
    AgentReferralLinkResponse,
    EligibleAgent,
    PublicAgentProfile,
    PublicAgentProfileList,
    PublicAgentProfileSummary,
    SlugAvailability,
)
from keeper_api.schemas.leads import (
    AgentLeadDetail,
    AgentLeadListResponse,
    AgentLeadSummary,
    ConsentState,
)
from keeper_api.schemas.lifecycle import AgentStatusResponse, AgentTransitionRequest
from keeper_api.services.agent_photos import (
    AgentPhotoRejected,
    MalwareScannerUnavailable,
    audit_target_id,
    delete_agent_photo,
    photo_id_for,
    photo_id_from_url,
    photo_url,
    read_agent_photo,
    store_agent_photo,
)
from keeper_api.services.agents import (
    AgentProfileConflict,
    AgentProfileLifecycleService,
    InvalidAgentProfileTransition,
    admin_profiles,
    create_profile,
    eligible_agent_accounts,
    ensure_referral_link,
    get_admin_profile,
    public_profile_by_slug,
    public_profiles,
    rotate_referral_link,
    slug_is_available,
    update_profile,
)
from keeper_api.services.audit import AuditService
from keeper_api.services.auth import (
    Principal,
    get_current_principal,
    require_admin,
    require_admin_aal2,
)
from keeper_api.services.borrower_authorization import require_agent_role_access
from keeper_api.services.consent_registry import MARKETING_CONSENT, SERVICE_CONTACT_CONSENT
from keeper_api.services.leads import (
    LeadInquiryNotFound,
    get_agent_lead,
    list_agent_leads,
)
from keeper_api.services.storage import StorageError

router = APIRouter(tags=["agents"])
NO_STORE = {"Cache-Control": "no-store"}
PHOTO_READ_CHUNK_BYTES = 64 * 1024
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DENIED_AGENT_PRINCIPAL_STATUSES = {
    CandidateStatus.DECLINED,
    CandidateStatus.WITHDRAWN,
    CandidateStatus.SUSPENDED,
    CandidateStatus.OFFBOARDING,
    CandidateStatus.OFFBOARDED,
}


def require_agent_profile_admin(
    principal: Principal = Depends(require_admin),
) -> Principal:
    if principal.candidate_status in DENIED_AGENT_PRINCIPAL_STATUSES:
        raise HTTPException(status_code=403, detail="agent profile access is unavailable")
    return principal


def _admin(profile: AgentProfile) -> AdminAgentProfile:
    return AdminAgentProfile.model_validate(profile, from_attributes=True)


def _release_replaced_photo(
    db: Session, settings: Settings, previous_url: str | None, current_url: str | None
) -> None:
    """Delete the previous Keeper-managed photo object once no profile uses it."""
    previous_photo_id = photo_id_from_url(settings, previous_url)
    if previous_photo_id is None:
        return
    if previous_photo_id == photo_id_from_url(settings, current_url):
        return
    still_referenced = db.scalar(
        select(AgentProfile.id).where(AgentProfile.photo_url == previous_url)
    )
    if still_referenced is not None:
        return
    delete_agent_photo(settings, previous_photo_id)


@router.get(
    "/agents",
    response_model=PublicAgentProfileList,
    responses={422: {"description": "Invalid pagination"}},
)
def list_public_agent_profiles(
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> PublicAgentProfileList:
    response.headers.update(NO_STORE)
    rows, total = public_profiles(db, limit=limit, offset=offset)
    return PublicAgentProfileList(
        items=[
            PublicAgentProfileSummary.model_validate(item, from_attributes=True) for item in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/agents/{slug}",
    response_model=PublicAgentProfile,
    responses={
        404: {"description": "Published profile not found"},
        422: {"description": "Invalid request"},
    },
)
def get_public_agent_profile(
    slug: str, response: Response, db: Session = Depends(get_db)
) -> PublicAgentProfile:
    response.headers.update(NO_STORE)
    profile = None
    if len(slug) <= 100 and SLUG.fullmatch(slug):
        profile = public_profile_by_slug(db, slug)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    return PublicAgentProfile.model_validate(profile, from_attributes=True)


@router.get(
    "/admin/agent-profiles",
    response_model=AdminAgentProfileList,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        422: {"description": "Invalid pagination"},
    },
)
def list_admin_agent_profiles(
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    _: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AdminAgentProfileList:
    response.headers.update(NO_STORE)
    rows, total = admin_profiles(db, limit=limit, offset=offset)
    return AdminAgentProfileList(
        items=[_admin(item) for item in rows], total=total, limit=limit, offset=offset
    )


@router.get(
    "/admin/eligible-agents",
    response_model=list[EligibleAgent],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
    },
)
def list_eligible_agents(
    response: Response,
    _: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> list[EligibleAgent]:
    response.headers.update(NO_STORE)
    return [
        EligibleAgent(user_id=user.id, display_name=user.display_name, email=user.email)
        for user in eligible_agent_accounts(db)
    ]


@router.get(
    "/admin/agent-profiles/slug-availability",
    response_model=SlugAvailability,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        422: {"description": "Invalid slug"},
    },
)
def agent_slug_availability(
    response: Response,
    slug: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        ),
    ],
    _: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> SlugAvailability:
    response.headers.update(NO_STORE)
    return SlugAvailability(slug=slug, available=slug_is_available(db, slug))


@router.post(
    "/admin/agent-profiles",
    response_model=AdminAgentProfile,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        404: {"description": "Active agent relationship not found"},
        409: {"description": "Profile user or slug conflict"},
        422: {"description": "Invalid profile content"},
    },
)
def create_admin_agent_profile(
    payload: AgentProfileCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AdminAgentProfile:
    response.headers.update(NO_STORE)
    try:
        return _admin(
            create_profile(
                db,
                payload,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc), headers=NO_STORE) from exc
    except AgentProfileConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc


@router.get(
    "/admin/agent-profiles/{profile_id}",
    response_model=AdminAgentProfile,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        404: {"description": "Profile not found"},
        422: {"description": "Invalid profile id"},
    },
)
def get_admin_agent_profile(
    profile_id: uuid.UUID,
    response: Response,
    _: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AdminAgentProfile:
    response.headers.update(NO_STORE)
    profile = get_admin_profile(db, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    return _admin(profile)


@router.patch(
    "/admin/agent-profiles/{profile_id}",
    response_model=AdminAgentProfile,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        404: {"description": "Profile not found"},
        409: {"description": "Profile lifecycle or slug conflict"},
        422: {"description": "Invalid profile content"},
    },
)
def patch_admin_agent_profile(
    profile_id: uuid.UUID,
    payload: AgentProfileUpdate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AdminAgentProfile:
    response.headers.update(NO_STORE)
    profile = get_admin_profile(db, profile_id, lock=True)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    previous_photo_url = profile.photo_url
    try:
        updated = update_profile(
            db,
            profile,
            payload,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except AgentProfileConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc
    _release_replaced_photo(db, settings, previous_photo_url, updated.photo_url)
    return _admin(updated)


async def _read_photo_bounded(file: UploadFile, maximum: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(min(PHOTO_READ_CHUNK_BYTES, maximum + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        if total > maximum:
            raise HTTPException(status_code=413, detail="photo is too large", headers=NO_STORE)
        chunks.append(chunk)
    return b"".join(chunks)


@router.post(
    "/admin/agent-photos",
    response_model=AgentPhotoUpload,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        413: {"description": "Photo exceeds the configured size limit"},
        415: {"description": "Photo type is unsupported"},
        422: {"description": "Photo is empty, malformed, or contains malware"},
        503: {"description": "Malware scanner or object storage is unavailable"},
    },
)
async def upload_admin_agent_photo(
    request: Request,
    response: Response,
    file: UploadFile = File(),
    principal: Principal = Depends(require_agent_profile_admin),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> AgentPhotoUpload:
    """Store one approved public agent photo and return its stable HTTPS URL.

    The object is written to the private bucket under the approved prefix and is
    reachable only through `GET /api/v1/agent-photos/{photo_id}`.
    """
    response.headers.update(NO_STORE)
    try:
        content = await _read_photo_bounded(file, settings.agent_photo_max_bytes)
        try:
            stored = await run_in_threadpool(
                request.app.state.document_scan_gate.run,
                lambda: store_agent_photo(
                    settings,
                    content=content,
                    filename=file.filename,
                    content_type=file.content_type,
                ),
            )
        except AgentPhotoRejected as exc:
            if exc.code == "file_too_large":
                raise HTTPException(
                    status_code=413, detail="photo is too large", headers=NO_STORE
                ) from exc
            unsupported = exc.code in {
                "declared_mime_mismatch",
                "detected_mime_mismatch",
                "invalid_filename",
                "unsupported_extension",
            }
            raise HTTPException(
                status_code=415 if unsupported else 422,
                detail="photo type is unsupported" if unsupported else "photo was rejected",
                headers=NO_STORE,
            ) from exc
        except MalwareScannerUnavailable as exc:
            raise HTTPException(
                status_code=503, detail="photo scanning is unavailable", headers=NO_STORE
            ) from exc
        except StorageError as exc:
            raise HTTPException(
                status_code=503, detail="photo storage is unavailable", headers=NO_STORE
            ) from exc
        photo_id = photo_id_for(stored.object_key)
        AuditService(db).record(
            "agent_photo.stored",
            "agent_photo",
            audit_target_id(photo_id),
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
            safe_metadata={
                "content_type": "image/jpeg" if photo_id.endswith(".jpg") else "image/png",
                "size_bytes": stored.size_bytes,
            },
        )
        db.commit()
        return AgentPhotoUpload(photo_url=photo_url(settings, photo_id))
    finally:
        await file.close()


@router.get(
    "/agent-photos/{photo_id}",
    response_class=Response,
    responses={
        200: {
            "description": "Approved public agent photo bytes",
            "content": {"image/jpeg": {}, "image/png": {}},
        },
        404: {"description": "Photo not found"},
    },
)
def get_public_agent_photo(
    photo_id: str,
    settings: Settings = Depends(get_settings),
) -> Response:
    """Serve one approved public agent photo; this is the only public read path.

    Only `public/agent-photos/` objects with a generated identifier are servable.
    An unknown or malformed identifier is indistinguishable from a missing one.
    """
    try:
        content, content_type = read_agent_photo(settings, photo_id)
    except (AgentPhotoRejected, StorageError) as exc:
        raise HTTPException(status_code=404, detail="agent photo was not found") from exc
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/agents/{profile_id}/status",
    response_model=AgentStatusResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin, MFA, or approval denied"},
        404: {"description": "Profile not found"},
        409: {"description": "Invalid profile transition"},
        422: {"description": "Invalid transition request"},
    },
)
def transition_agent_profile(
    profile_id: uuid.UUID,
    payload: AgentTransitionRequest,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AgentStatusResponse:
    response.headers.update(NO_STORE)
    profile = get_admin_profile(db, profile_id, lock=True)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    try:
        AgentProfileLifecycleService(db).transition(
            profile,
            payload.status,
            actor_user_id=principal.user_id,
            actor_can_approve="brokerage_admin" in principal.roles,
            reason=payload.reason,
            request_id=request.state.request_id,
        )
    except InvalidAgentProfileTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc
    return AgentStatusResponse(status=payload.status)


def _referral_out(link: AgentReferralLink, settings: Settings) -> AgentReferralLinkResponse:
    base = (settings.borrower_application_origin or "https://apply.keeperfinancial.ca").rstrip("/")
    return AgentReferralLinkResponse(
        user_id=link.user_id,
        code=link.code,
        # The wizard, not the landing page: the origin root does not read ?agent=.
        apply_url=f"{base}/mortgage-application?agent={link.code}",
        created_at=link.created_at,
        rotated_at=link.rotated_at,
    )


@router.get(
    "/agent-referral-link",
    response_model=AgentReferralLinkResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Agent access is required"},
    },
)
def get_own_referral_link(
    response: Response,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AgentReferralLinkResponse:
    """The signed-in agent's own application link, minted on first read."""
    response.headers.update(NO_STORE)
    if "agent" not in principal.roles or not principal.is_active:
        raise HTTPException(status_code=403, detail="agent access is required")
    try:
        link = ensure_referral_link(db, principal.user_id, created_by_user_id=principal.user_id)
    except LookupError as exc:
        raise HTTPException(status_code=403, detail="agent access is unavailable") from exc
    return _referral_out(link, settings)


@router.get(
    "/admin/agent-accounts/{user_id}/referral-link",
    response_model=AgentReferralLinkResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Agent account not found"},
    },
)
def get_agent_referral_link(
    user_id: uuid.UUID,
    response: Response,
    _: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AgentReferralLinkResponse:
    response.headers.update(NO_STORE)
    try:
        link = ensure_referral_link(db, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="agent account not found") from exc
    return _referral_out(link, settings)


@router.post(
    "/admin/agent-accounts/{user_id}/referral-link/rotate",
    response_model=AgentReferralLinkResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Agent account not found"},
    },
)
def rotate_agent_referral_link(
    user_id: uuid.UUID,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin_aal2),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AgentReferralLinkResponse:
    """Replace an agent's code; the previous link stops resolving immediately."""
    response.headers.update(NO_STORE)
    try:
        link = rotate_referral_link(
            db,
            user_id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="agent account not found") from exc
    except AgentProfileConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _referral_out(link, settings)


# --------------------------------------------------------------------------- #
# Agent-owned lead inquiries
# --------------------------------------------------------------------------- #


def _lead_consent(consent: object | None) -> ConsentState | None:
    from keeper_api.models.domain import ConsentRecord

    if not isinstance(consent, ConsentRecord):
        return None
    return ConsentState(
        state="withdrawn" if consent.withdrawn_at else "granted",
        granted_at=consent.granted_at,
        withdrawn_at=consent.withdrawn_at,
    )


@router.get(
    "/agent/leads",
    response_model=AgentLeadListResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Agent access with MFA is required"},
    },
)
def agent_leads(
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AgentLeadListResponse:
    """Inquiries assigned to the signed-in agent account only."""
    response.headers.update(NO_STORE)
    require_agent_role_access(principal, db, settings)
    leads, _consents, total = list_agent_leads(
        db, agent_user_id=principal.user_id, limit=limit, offset=offset
    )
    return AgentLeadListResponse(
        items=[
            AgentLeadSummary(
                id=lead.id,
                name=lead.name,
                mortgage_objective=lead.mortgage_objective,
                preferred_contact_method=lead.preferred_contact_method,
                status=lead.status,
                assigned_at=lead.assigned_at,
                created_at=lead.created_at,
            )
            for lead in leads
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/agent/leads/{lead_id}",
    response_model=AgentLeadDetail,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Agent access with MFA is required"},
        404: {"description": "Lead unavailable"},
    },
)
def agent_lead_detail(
    lead_id: uuid.UUID,
    request: Request,
    response: Response,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AgentLeadDetail:
    """Full contact details for one inquiry assigned to this agent."""
    response.headers.update(NO_STORE)
    require_agent_role_access(principal, db, settings)
    try:
        lead, consents = get_agent_lead(
            db,
            lead_id=lead_id,
            agent_user_id=principal.user_id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LeadInquiryNotFound as exc:
        raise HTTPException(status_code=404, detail="lead is unavailable") from exc
    service_consent = _lead_consent(consents.get(SERVICE_CONTACT_CONSENT.purpose))
    if service_consent is None:
        raise HTTPException(
            status_code=500,
            detail="lead consent evidence is unavailable",
            headers=NO_STORE,
        )
    return AgentLeadDetail(
        id=lead.id,
        name=lead.name,
        email=lead.email,
        telephone=lead.telephone,
        mortgage_objective=lead.mortgage_objective,
        preferred_contact_method=lead.preferred_contact_method,
        message=lead.message,
        status=lead.status,
        assigned_at=lead.assigned_at,
        created_at=lead.created_at,
        service_consent=service_consent,
        marketing_consent=_lead_consent(consents.get(MARKETING_CONSENT.purpose)),
    )
