from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MediaCreate(BaseModel):
    post_id: int
    type: str  # "image", "video", "file"
    url: str
    filename: Optional[str] = None


class MediaResponse(BaseModel):
    id: int
    post_id: int
    type: str
    url: str
    filename: Optional[str]
    corruption_level: int
    created_at: datetime

    model_config = {"from_attributes": True}
