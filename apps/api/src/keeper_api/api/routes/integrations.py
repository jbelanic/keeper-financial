from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from keeper_api.core.config import Settings, get_settings
from keeper_api.integrations.mortgage_application import (
    MortgageApplicationAdapter,
    MortgageApplicationUnavailable,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get(
    "/mortgage-application",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    response_class=RedirectResponse,
    responses={503: {"description": "Configured application destination unavailable"}},
)
def mortgage_application_redirect(
    agent: str | None = Query(default=None, pattern=r"^[a-z0-9-]{1,100}$"),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    try:
        destination = MortgageApplicationAdapter(settings).redirect_url(agent)
    except MortgageApplicationUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return RedirectResponse(destination, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
