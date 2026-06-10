import uuid
from datetime import datetime

from pydantic import BaseModel


class QRCodeOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    redirect_url: str
    svg_url: str | None
    png_url: str | None
    scan_count: int

    model_config = {"from_attributes": True}
