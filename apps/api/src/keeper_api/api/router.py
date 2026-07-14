from fastapi import APIRouter

from keeper_api.api.routes import agents, auth, candidates, documents, integrations, leads

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(integrations.router)
api_router.include_router(candidates.router)
api_router.include_router(agents.router)
api_router.include_router(documents.router)
