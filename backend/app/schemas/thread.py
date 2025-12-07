from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.schemas.post import PostResponse


class ThreadCreate(BaseModel):
    board_id: int
    title: str


class ThreadUpdate(BaseModel):
    title: Optional[str] = None
    is_sticky: Optional[bool] = None
    is_locked: Optional[bool] = None


class ThreadResponse(BaseModel):
    id: int
    board_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    is_sticky: bool
    is_locked: bool
    anomaly_level: int

    model_config = {"from_attributes": True}


class ThreadListItem(ThreadResponse):
    post_count: int = 0
    last_post_at: Optional[datetime] = None
