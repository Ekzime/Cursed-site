from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.repositories.thread_repository import ThreadRepository
from app.schemas.post import PostCreate, PostUpdate, PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    description="Get a post by ID"
)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new post"
)
async def create_post(
    data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if thread exists
    thread_repo = ThreadRepository(db)
    thread = await thread_repo.get_by_id(data.thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Check if thread is locked
    if thread.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Thread is locked"
        )

    post_repo = PostRepository(db)
    post = await post_repo.create(
        thread_id=data.thread_id,
        user_id=current_user.id,
        content=data.content,
    )
    return post


@router.put(
    "/{post_id}",
    response_model=PostResponse,
    description="Update a post"
)
async def update_post(
    post_id: int,
    data: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check ownership
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own posts"
        )

    updated_post = await repo.update(post_id, content=data.content)
    return updated_post


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a post"
)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check ownership
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts"
        )

    await repo.delete(post_id)


@router.get(
    "/user/{user_id}",
    response_model=List[PostResponse],
    description="Get posts by user"
)
async def get_posts_by_user(
    user_id: int,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    repo = PostRepository(db)
    posts = await repo.get_by_user(user_id, limit, offset)
    return posts
