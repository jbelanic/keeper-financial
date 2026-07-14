import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name)


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    responses={503: {"model": DatabaseHealthResponse}},
)
def database_health(response: Response, db: Session = Depends(get_db)) -> DatabaseHealthResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("database health check failed", extra={"event": "health.db_unavailable"})
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealthResponse(status="unavailable", database="unreachable")
    return DatabaseHealthResponse(status="ok", database="reachable")
