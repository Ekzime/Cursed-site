from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.board_repository import BoardRepository
from app.schemas.board import BoardCreate, BoardUpdate, BoardResponse, BoardWithThreadCount

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get(
    "",
    response_model=List[BoardResponse],
    description="Get all visible boards"
)
async def get_boards(db: AsyncSession = Depends(get_db)):
    repo = BoardRepository(db)
    boards = await repo.get_visible_boards()
    return boards


@router.get(
    "/{board_id}",
    response_model=BoardResponse,
    description="Get a board by ID"
)
async def get_board(board_id: int, db: AsyncSession = Depends(get_db)):
    repo = BoardRepository(db)
    board = await repo.get_by_id(board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return board


@router.get(
    "/slug/{slug}",
    response_model=BoardResponse,
    description="Get a board by slug"
)
async def get_board_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    repo = BoardRepository(db)
    board = await repo.get_by_slug(slug)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return board


@router.post(
    "",
    response_model=BoardResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new board"
)
async def create_board(data: BoardCreate, db: AsyncSession = Depends(get_db)):
    repo = BoardRepository(db)

    # Check if slug already exists
    existing = await repo.get_by_slug(data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Board with this slug already exists"
        )

    board = await repo.create(
        slug=data.slug,
        name=data.name,
        description=data.description,
        is_hidden=data.is_hidden,
        unlock_trigger=data.unlock_trigger,
    )
    return board


@router.put(
    "/{board_id}",
    response_model=BoardResponse,
    description="Update a board"
)
async def update_board(
    board_id: int,
    data: BoardUpdate,
    db: AsyncSession = Depends(get_db)
):
    repo = BoardRepository(db)
    board = await repo.update(
        board_id,
        name=data.name,
        description=data.description,
        is_hidden=data.is_hidden,
        unlock_trigger=data.unlock_trigger,
    )
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return board


@router.delete(
    "/{board_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a board"
)
async def delete_board(board_id: int, db: AsyncSession = Depends(get_db)):
    repo = BoardRepository(db)
    deleted = await repo.delete(board_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
