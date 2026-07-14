import uuid

from pydantic import BaseModel


class AccessResponse(BaseModel):
    allowed: bool
    area: str
    user_id: uuid.UUID
    roles: list[str]
