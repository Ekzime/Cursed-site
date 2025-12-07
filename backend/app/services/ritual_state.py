"""
RitualState manager for Redis operations.
Handles CRUD operations for user ritual states.
"""

import json
from datetime import datetime
from typing import Optional, Tuple

import redis.asyncio as redis

from app.schemas.ritual import RitualState


class RitualStateManager:
    """
    Manages RitualState storage in Redis.

    Key format: ritual_state:{user_id}
    TTL: 24 hours (configurable)
    """

    KEY_PREFIX = "ritual_state:"
    DEFAULT_TTL = 86400  # 24 hours

    def __init__(self, redis_client: redis.Redis, ttl: int = DEFAULT_TTL):
        self.redis = redis_client
        self.ttl = ttl

    def _key(self, user_id: str) -> str:
        """Generate Redis key for user."""
        return f"{self.KEY_PREFIX}{user_id}"

    async def get(self, user_id: str) -> Optional[RitualState]:
        """
        Get RitualState from Redis.

        Args:
            user_id: User identifier

        Returns:
            RitualState if exists, None otherwise
        """
        key = self._key(user_id)
        data = await self.redis.get(key)

        if not data:
            return None

        try:
            state_dict = json.loads(data)
            return RitualState.from_redis_dict(state_dict)
        except (json.JSONDecodeError, ValueError):
            # Corrupted data, remove and return None
            await self.redis.delete(key)
            return None

    async def create(self, user_id: str) -> RitualState:
        """
        Create new RitualState for user.

        Args:
            user_id: User identifier

        Returns:
            Newly created RitualState
        """
        now = datetime.utcnow()
        state = RitualState(
            user_id=user_id,
            first_visit=now,
            last_activity=now,
        )
        await self.save(state)
        return state

    async def get_or_create(self, user_id: str) -> Tuple[RitualState, bool]:
        """
        Get existing RitualState or create new one.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (RitualState, is_new)
        """
        state = await self.get(user_id)
        if state:
            return state, False
        return await self.create(user_id), True

    async def save(self, state: RitualState) -> None:
        """
        Save RitualState to Redis with TTL.

        Args:
            state: RitualState to save
        """
        # Update last_activity
        state.last_activity = datetime.utcnow()

        key = self._key(state.user_id)
        data = json.dumps(state.to_redis_dict())

        await self.redis.setex(key, self.ttl, data)

    async def update_progress(self, user_id: str, delta: int) -> Optional[RitualState]:
        """
        Increment/decrement progress.

        Args:
            user_id: User identifier
            delta: Amount to change (can be negative)

        Returns:
            Updated RitualState or None if not found
        """
        state = await self.get(user_id)
        if not state:
            return None

        state.progress = max(0, min(100, state.progress + delta))
        await self.save(state)
        return state

    async def set_progress(self, user_id: str, progress: int) -> Optional[RitualState]:
        """
        Set progress to specific value.

        Args:
            user_id: User identifier
            progress: New progress value (0-100)

        Returns:
            Updated RitualState or None if not found
        """
        state = await self.get(user_id)
        if not state:
            return None

        state.progress = max(0, min(100, progress))
        await self.save(state)
        return state

    async def add_viewed_thread(self, user_id: str, thread_id: int) -> Optional[RitualState]:
        """
        Record that user viewed a thread.

        Args:
            user_id: User identifier
            thread_id: Thread ID

        Returns:
            Updated RitualState or None if not found
        """
        state = await self.get(user_id)
        if not state:
            return None

        if thread_id not in state.viewed_threads:
            state.viewed_threads.append(thread_id)
            # Keep only last 100 threads
            if len(state.viewed_threads) > 100:
                state.viewed_threads = state.viewed_threads[-100:]

        await self.save(state)
        return state

    async def add_viewed_post(self, user_id: str, post_id: int) -> Optional[RitualState]:
        """
        Record that user viewed a post.

        Args:
            user_id: User identifier
            post_id: Post ID

        Returns:
            Updated RitualState or None if not found
        """
        state = await self.get(user_id)
        if not state:
            return None

        if post_id not in state.viewed_posts:
            state.viewed_posts.append(post_id)
            # Keep only last 500 posts
            if len(state.viewed_posts) > 500:
                state.viewed_posts = state.viewed_posts[-500:]

        await self.save(state)
        return state

    async def add_trigger(self, user_id: str, trigger: str) -> Optional[RitualState]:
        """
        Mark trigger as hit.

        Args:
            user_id: User identifier
            trigger: Trigger name

        Returns:
            Updated RitualState or None if not found
        """
        state = await self.get(user_id)
        if not state:
            return None

        state.triggers_hit.add(trigger)
        await self.save(state)
        return state

    async def add_time_on_site(self, user_id: str, seconds: int) -> Optional[RitualState]:
        """
        Add time spent on site.

        Args:
            user_id: User identifier
            seconds: Seconds to add

        Returns:
            Updated RitualState or None if not found
        """
        state = await self.get(user_id)
        if not state:
            return None

        state.time_on_site += seconds
        await self.save(state)
        return state

    async def update_known_patterns(
        self, user_id: str, key: str, value: any
    ) -> Optional[RitualState]:
        """
        Update known patterns (personalization data).

        Args:
            user_id: User identifier
            key: Pattern key
            value: Pattern value

        Returns:
            Updated RitualState or None if not found
        """
        state = await self.get(user_id)
        if not state:
            return None

        state.known_patterns[key] = value
        await self.save(state)
        return state

    async def delete(self, user_id: str) -> bool:
        """
        Delete RitualState.

        Args:
            user_id: User identifier

        Returns:
            True if deleted, False if not found
        """
        key = self._key(user_id)
        result = await self.redis.delete(key)
        return result > 0

    async def exists(self, user_id: str) -> bool:
        """
        Check if RitualState exists.

        Args:
            user_id: User identifier

        Returns:
            True if exists
        """
        key = self._key(user_id)
        return await self.redis.exists(key) > 0

    async def get_all_user_ids(self) -> list[str]:
        """
        Get all user IDs with active RitualState.
        Use with caution in production (KEYS command).

        Returns:
            List of user IDs
        """
        pattern = f"{self.KEY_PREFIX}*"
        keys = await self.redis.keys(pattern)
        return [key.replace(self.KEY_PREFIX, "") for key in keys]

    async def refresh_ttl(self, user_id: str) -> bool:
        """
        Refresh TTL for user's RitualState.

        Args:
            user_id: User identifier

        Returns:
            True if refreshed, False if not found
        """
        key = self._key(user_id)
        return await self.redis.expire(key, self.ttl)
