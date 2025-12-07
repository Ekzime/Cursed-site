from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, email: str, hashed_password: str) -> User:
        """Create a new user in the database.

        Args:
            username (str): The username of the new user.
            email (str): The email of the new user.
            hashed_password (str): The hashed password of the new user.
        Returns:
            User: The created user object.
        """
        new_user = User(username=username, email=email, hashed_password=hashed_password)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user


    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.
        Returns:
            Optional[User]: The user object if found, else None.
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by their username.

        Args:
            username (str): The username of the user to retrieve.
        Returns:
            user (User): The user object if found.
        """
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
