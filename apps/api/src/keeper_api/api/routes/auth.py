from typing import Literal

from fastapi import APIRouter, Depends

from keeper_api.core.config import Settings, get_settings
from keeper_api.schemas.auth import AccessResponse
from keeper_api.services.auth import Principal, authorize_portal, get_current_principal

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/access", response_model=AccessResponse)
def portal_access(
    area: Literal["candidate", "admin"],
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> AccessResponse:
    authorize_portal(principal, area, settings)
    return AccessResponse(
        allowed=True,
        area=area,
        user_id=principal.user_id,
        roles=sorted(principal.roles),
    )
