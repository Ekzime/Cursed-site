from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.repositories.thread_repository import ThreadRepository
from app.repositories.board_repository import BoardRepository
from app.repositories.post_repository import PostRepository
from app.schemas.thread import ThreadCreate, ThreadUpdate, ThreadResponse, ThreadListItem
from app.schemas.post import PostResponse

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get(
    "/board/{board_id}",
    response_model=List[ThreadListItem],
    description="Get threads by board ID"
)
async def get_threads_by_board(
    board_id: int,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    # Check if board exists
    board_repo = BoardRepository(db)
    board = await board_repo.get_by_id(board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    thread_repo = ThreadRepository(db)
    threads_data = await thread_repo.get_threads_with_post_counts(board_id, limit, offset)

    result = []
    for data in threads_data:
        thread = data["thread"]
        result.append(ThreadListItem(
            id=thread.id,
            board_id=thread.board_id,
            title=thread.title,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            is_sticky=thread.is_sticky,
            is_locked=thread.is_locked,
            anomaly_level=thread.anomaly_level,
            post_count=data["post_count"],
            last_post_at=data["last_post_at"],
        ))

    return result


@router.get(
    "/{thread_id}",
    response_model=ThreadResponse,
    description="Get a thread by ID"
)
async def get_thread(thread_id: int, db: AsyncSession = Depends(get_db)):
    repo = ThreadRepository(db)
    thread = await repo.get_by_id(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    return thread


@router.get(
    "/{thread_id}/posts",
    response_model=List[PostResponse],
    description="Get posts in a thread"
)
async def get_thread_posts(
    thread_id: int,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    # Check if thread exists
    thread_repo = ThreadRepository(db)
    thread = await thread_repo.get_by_id(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    post_repo = PostRepository(db)
    posts = await post_repo.get_by_thread(thread_id, limit, offset)
    return posts


@router.post(
    "",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new thread"
)
async def create_thread(
    data: ThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if board exists
    board_repo = BoardRepository(db)
    board = await board_repo.get_by_id(data.board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    # Check if board is hidden and user has access
    if board.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create thread in hidden board"
        )

    thread_repo = ThreadRepository(db)
    thread = await thread_repo.create(
        board_id=data.board_id,
        title=data.title,
    )
    return thread


@router.put(
    "/{thread_id}",
    response_model=ThreadResponse,
    description="Update a thread"
)
async def update_thread(
    thread_id: int,
    data: ThreadUpdate,
    db: AsyncSession = Depends(get_db)
):
    repo = ThreadRepository(db)
    thread = await repo.update(
        thread_id,
        title=data.title,
        is_sticky=data.is_sticky,
        is_locked=data.is_locked,
    )
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    return thread


@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a thread"
)
async def delete_thread(thread_id: int, db: AsyncSession = Depends(get_db)):
    repo = ThreadRepository(db)
    deleted = await repo.delete(thread_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
