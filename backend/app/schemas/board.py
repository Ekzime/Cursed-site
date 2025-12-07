from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BoardCreate(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    is_hidden: bool = False
    unlock_trigger: Optional[str] = None


class BoardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_hidden: Optional[bool] = None
    unlock_trigger: Optional[str] = None


class BoardResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: Optional[str]
    is_hidden: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BoardWithThreadCount(BoardResponse):
    thread_count: int = 0
