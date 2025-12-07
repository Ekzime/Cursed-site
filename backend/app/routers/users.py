from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.core.database import get_db
from app.core.auth import hash_password
from app.repositories.user_repository import UserRepository

import logging
from typing import Optional

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    description="Create a new user"
)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(session=db)

    # Check if username already exists
    existing_user = await repo.get_user_by_username(data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    try:
        user = await repo.create_user(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password)
        )
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )


@router.get(
    path="/{user_id}",
    response_model=UserResponse,
    description="Get user by ID"
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(session=db)
    user = await repo.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
