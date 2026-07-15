from fastapi import APIRouter

from keeper_api.api.routes import (
    agents,
    auth,
    candidate_applications,
    candidate_documents,
    documents,
    integrations,
    leads,
    recruitment,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(integrations.router)
api_router.include_router(recruitment.router)
api_router.include_router(candidate_applications.router)
api_router.include_router(candidate_applications.privacy_router)
api_router.include_router(candidate_documents.router)
api_router.include_router(agents.router)
api_router.include_router(documents.router)
