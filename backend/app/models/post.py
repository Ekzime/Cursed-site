from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.thread import Thread
    from app.models.user import User
    from app.models.media import Media


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    thread_id: Mapped[int] = Column(Integer, ForeignKey("threads.id"), nullable=False, index=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = Column(Text, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_anomaly: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    anomaly_type: Mapped[Optional[str]] = Column(String(50), nullable=True)

    # Relationships
    thread: Mapped["Thread"] = relationship("Thread", back_populates="posts")
    user: Mapped["User"] = relationship("User", back_populates="posts")
    media: Mapped[List["Media"]] = relationship("Media", back_populates="post")
