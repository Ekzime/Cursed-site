"""
Ritual Middleware for user identification and state management.
Extracts user identity from fingerprint/cookie and attaches RitualState to request.
"""

import uuid
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import redis.asyncio as redis

from app.services.ritual_state import RitualStateManager
from app.schemas.ritual import RitualState


# Constants
FINGERPRINT_HEADER = "X-Fingerprint"
RITUAL_COOKIE = "ritual_id"
COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year


class RitualMiddleware(BaseHTTPMiddleware):
    """
    Middleware that identifies users and manages RitualState.

    User identification priority:
    1. X-Fingerprint header (from frontend fingerprinting)
    2. ritual_id cookie
    3. Generate new UUID (set as cookie)

    Attaches to request.state:
    - ritual_user_id: str - User identifier
    - ritual_state: RitualState - User's ritual state
    - is_new_visitor: bool - True if first visit
    """

    def __init__(self, app, ttl: int = 86400):
        super().__init__(app)
        self.ttl = ttl
        self._state_manager: Optional[RitualStateManager] = None

    async def _get_state_manager(self, request: Request) -> Optional[RitualStateManager]:
        """Get or create RitualStateManager using Redis from app state."""
        if self._state_manager is None:
            # Get Redis from app.state (set during lifespan)
            redis_client = getattr(request.app.state, "redis", None)
            if redis_client:
                self._state_manager = RitualStateManager(redis_client, ttl=self.ttl)
        return self._state_manager

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip for health checks and static files
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Extract or generate user ID
        user_id, need_cookie = self._get_user_id(request)

        # Initialize request state
        request.state.ritual_user_id = user_id
        request.state.ritual_state = None
        request.state.is_new_visitor = False

        # Get state manager (requires Redis to be initialized)
        state_manager = await self._get_state_manager(request)

        if user_id and state_manager:
            # Get or create RitualState
            state, is_new = await state_manager.get_or_create(user_id)
            request.state.ritual_state = state
            request.state.is_new_visitor = is_new

        # Process request
        response = await call_next(request)

        # Set cookie if needed
        if need_cookie and user_id:
            response.set_cookie(
                key=RITUAL_COOKIE,
                value=user_id,
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                samesite="lax",
                secure=False,  # Set to True in production with HTTPS
            )

        return response

    def _get_user_id(self, request: Request) -> tuple[Optional[str], bool]:
        """
        Extract user ID from request.

        Returns:
            Tuple of (user_id, need_to_set_cookie)
        """
        # Priority 1: Fingerprint header
        fingerprint = request.headers.get(FINGERPRINT_HEADER)
        if fingerprint:
            return fingerprint, False

        # Priority 2: Existing cookie
        cookie = request.cookies.get(RITUAL_COOKIE)
        if cookie:
            return cookie, False

        # Priority 3: Generate new UUID
        new_id = str(uuid.uuid4())
        return new_id, True

    def _should_skip(self, path: str) -> bool:
        """Check if path should skip ritual tracking."""
        skip_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
        ]
        return any(path.startswith(p) for p in skip_paths)


# FastAPI dependencies for accessing ritual state in routes


async def get_ritual_state(request: Request) -> Optional[RitualState]:
    """
    FastAPI dependency to get current user's RitualState.

    Usage:
        @router.get("/example")
        async def example(state: RitualState = Depends(get_ritual_state)):
            if state:
                print(f"Progress: {state.progress}")
    """
    return getattr(request.state, "ritual_state", None)


async def get_ritual_user_id(request: Request) -> Optional[str]:
    """
    FastAPI dependency to get current ritual user ID.

    Usage:
        @router.get("/example")
        async def example(user_id: str = Depends(get_ritual_user_id)):
            if user_id:
                print(f"User: {user_id}")
    """
    return getattr(request.state, "ritual_user_id", None)


async def get_is_new_visitor(request: Request) -> bool:
    """
    FastAPI dependency to check if user is new.

    Usage:
        @router.get("/example")
        async def example(is_new: bool = Depends(get_is_new_visitor)):
            if is_new:
                print("Welcome, new visitor!")
    """
    return getattr(request.state, "is_new_visitor", False)
