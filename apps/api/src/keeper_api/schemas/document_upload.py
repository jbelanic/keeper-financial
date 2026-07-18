from typing import Literal

from pydantic import BaseModel


class DocumentScanResponse(BaseModel):
    status: Literal["clean"]
