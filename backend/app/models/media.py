from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    type: Mapped[str] = Column(String(20), nullable=False)  # "image", "video", "file"
    url: Mapped[str] = Column(String(500), nullable=False)
    filename: Mapped[str] = Column(String(255), nullable=True)
    corruption_level: Mapped[int] = Column(Integer, default=0, nullable=False)  # 0-10
    created_at: Mapped[datetime] = Column(DateTime, server_default=func.now())

    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="media")
