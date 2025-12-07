from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import Post
from app.repositories.base import BaseRepository


class PostRepository(BaseRepository[Post]):
    """Repository for Post model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Post)

    async def get_by_thread(
        self,
        thread_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Post]:
        """Get posts by thread ID with pagination."""
        result = await self.session.execute(
            select(Post)
            .where(Post.thread_id == thread_id)
            .order_by(Post.created_at)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_with_media(self, post_id: int) -> Optional[Post]:
        """Get a post with all its media."""
        result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.media))
            .where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Post]:
        """Get posts by user ID."""
        result = await self.session.execute(
            select(Post)
            .where(Post.user_id == user_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_thread(self, thread_id: int) -> int:
        """Count posts in a thread."""
        result = await self.session.execute(
            select(func.count(Post.id)).where(Post.thread_id == thread_id)
        )
        return result.scalar_one()

    async def mark_as_anomaly(self, post_id: int, anomaly_type: str) -> Optional[Post]:
        """Mark a post as an anomaly."""
        post = await self.get_by_id(post_id)
        if not post:
            return None
        post.is_anomaly = True
        post.anomaly_type = anomaly_type
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_anomaly_posts(self, thread_id: int) -> List[Post]:
        """Get all anomaly posts in a thread."""
        result = await self.session.execute(
            select(Post)
            .where(Post.thread_id == thread_id, Post.is_anomaly == True)
            .order_by(Post.created_at)
        )
        return list(result.scalars().all())
