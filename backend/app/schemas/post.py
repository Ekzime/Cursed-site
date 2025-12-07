from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.media import MediaResponse


class PostCreate(BaseModel):
    thread_id: int
    content: str


class PostUpdate(BaseModel):
    content: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    thread_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    is_anomaly: bool
    anomaly_type: Optional[str]

    model_config = {"from_attributes": True}


class PostWithUser(PostResponse):
    username: str
    avatar_url: Optional[str] = None


class PostWithMedia(PostResponse):
    media: List[MediaResponse] = []
