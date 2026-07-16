from fastapi import APIRouter

from keeper_api.api.routes import (
    auth,
    candidate_applications,
    candidate_documents,
    candidate_onboarding,
    documents,
    integrations,
    leads,
    onboarding,
    recruitment,
    review,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(integrations.router)
api_router.include_router(recruitment.router)
api_router.include_router(candidate_applications.router)
api_router.include_router(candidate_applications.privacy_router)
api_router.include_router(candidate_documents.router)
# NOTE: agents.router is intentionally NOT mounted. The agent-profile
# lifecycle transition route (POST /api/v1/agents/{profile_id}/status) is a
# Phase 1E operation and must remain unmounted until Phase 1E is scheduled
# (see docs/07 delivery plan and docs/19 Phase 1C policy boundary). Mounting
# it prematurely was Phase 1C audit finding B9.
api_router.include_router(documents.router)
api_router.include_router(review.router)
api_router.include_router(onboarding.router)
api_router.include_router(candidate_onboarding.router)
