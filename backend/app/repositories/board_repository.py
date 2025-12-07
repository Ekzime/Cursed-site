from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board import Board
from app.repositories.base import BaseRepository


class BoardRepository(BaseRepository[Board]):
    """Repository for Board model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Board)

    async def get_by_slug(self, slug: str) -> Optional[Board]:
        """Get a board by its slug."""
        result = await self.session.execute(
            select(Board).where(Board.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_visible_boards(self) -> List[Board]:
        """Get all non-hidden boards."""
        result = await self.session.execute(
            select(Board).where(Board.is_hidden == False).order_by(Board.name)
        )
        return list(result.scalars().all())

    async def get_all_boards(self, include_hidden: bool = False) -> List[Board]:
        """Get all boards, optionally including hidden ones."""
        query = select(Board).order_by(Board.name)
        if not include_hidden:
            query = query.where(Board.is_hidden == False)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_board_with_thread_count(self, board_id: int) -> Optional[dict]:
        """Get a board with its thread count."""
        from app.models.thread import Thread

        board = await self.get_by_id(board_id)
        if not board:
            return None

        count_result = await self.session.execute(
            select(func.count(Thread.id)).where(Thread.board_id == board_id)
        )
        thread_count = count_result.scalar_one()

        return {
            "board": board,
            "thread_count": thread_count,
        }
