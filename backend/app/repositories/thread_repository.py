from typing import List, Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.thread import Thread
from app.models.post import Post
from app.repositories.base import BaseRepository


class ThreadRepository(BaseRepository[Thread]):
    """Repository for Thread model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Thread)

    async def get_by_board(
        self,
        board_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Thread]:
        """Get threads by board ID with pagination."""
        result = await self.session.execute(
            select(Thread)
            .where(Thread.board_id == board_id)
            .order_by(desc(Thread.is_sticky), desc(Thread.updated_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_with_posts(self, thread_id: int) -> Optional[Thread]:
        """Get a thread with all its posts."""
        result = await self.session.execute(
            select(Thread)
            .options(selectinload(Thread.posts))
            .where(Thread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def count_by_board(self, board_id: int) -> int:
        """Count threads in a board."""
        result = await self.session.execute(
            select(func.count(Thread.id)).where(Thread.board_id == board_id)
        )
        return result.scalar_one()

    async def get_threads_with_post_counts(
        self,
        board_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[dict]:
        """Get threads with post counts and last post time."""
        threads = await self.get_by_board(board_id, limit, offset)
        result = []

        for thread in threads:
            # Get post count
            count_result = await self.session.execute(
                select(func.count(Post.id)).where(Post.thread_id == thread.id)
            )
            post_count = count_result.scalar_one()

            # Get last post time
            last_post_result = await self.session.execute(
                select(func.max(Post.created_at)).where(Post.thread_id == thread.id)
            )
            last_post_at = last_post_result.scalar_one()

            result.append({
                "thread": thread,
                "post_count": post_count,
                "last_post_at": last_post_at,
            })

        return result

    async def increment_anomaly_level(self, thread_id: int) -> Optional[Thread]:
        """Increment the anomaly level of a thread."""
        thread = await self.get_by_id(thread_id)
        if not thread:
            return None
        if thread.anomaly_level < 10:
            thread.anomaly_level += 1
        await self.session.commit()
        await self.session.refresh(thread)
        return thread
