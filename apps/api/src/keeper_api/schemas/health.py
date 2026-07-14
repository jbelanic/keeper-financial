from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class DatabaseHealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    database: Literal["reachable", "unreachable"]
