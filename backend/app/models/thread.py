from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.post import Post


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    board_id: Mapped[int] = Column(Integer, ForeignKey("boards.id"), nullable=False, index=True)
    title: Mapped[str] = Column(String(255), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_sticky: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    anomaly_level: Mapped[int] = Column(Integer, default=0, nullable=False)  # 0-10

    # Relationships
    board: Mapped["Board"] = relationship("Board", back_populates="threads")
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="thread", order_by="Post.created_at")
