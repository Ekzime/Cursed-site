from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    username: Mapped[str] = Column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = Column(String(500), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, server_default=func.now())

    # Anomaly fields (for NPC users)
    is_anomaly: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    anomaly_data: Mapped[Optional[dict]] = Column(JSON, nullable=True)

    # Relationships
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="user")
