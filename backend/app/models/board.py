from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.thread import Thread


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = Column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    is_hidden: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    unlock_trigger: Mapped[Optional[str]] = Column(String(50), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, server_default=func.now())

    # Relationships
    threads: Mapped[List["Thread"]] = relationship("Thread", back_populates="board")
