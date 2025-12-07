"""
Anomaly Queue for the Ritual Engine.
Redis-backed FIFO queue for delivering anomalies to WebSocket connections.
"""

import json
from typing import Optional, List
import redis.asyncio as redis

from app.schemas.anomaly import AnomalyEvent


class AnomalyQueue:
    """
    Redis-backed queue for anomaly events.

    Each user has their own queue: anomaly_queue:{user_id}
    Events are JSON-encoded and stored as Redis list items.

    Usage:
        queue = AnomalyQueue(redis_client)

        # Push event
        await queue.push(user_id, event)

        # Pop with blocking (for WebSocket listener)
        event = await queue.pop_blocking(user_id, timeout=30)

        # Push to multiple users
        await queue.push_to_all(user_ids, event)
    """

    KEY_PREFIX = "anomaly_queue:"
    DEFAULT_TTL = 3600  # 1 hour - queues expire if not consumed
    MAX_QUEUE_SIZE = 100  # Maximum events per user queue

    def __init__(self, redis_client: redis.Redis, ttl: int = DEFAULT_TTL):
        self.redis = redis_client
        self.ttl = ttl

    def _key(self, user_id: str) -> str:
        """Generate Redis key for user's queue."""
        return f"{self.KEY_PREFIX}{user_id}"

    async def push(self, user_id: str, event: AnomalyEvent) -> int:
        """
        Push anomaly event to user's queue.

        Args:
            user_id: User identifier
            event: AnomalyEvent to queue

        Returns:
            Queue length after push
        """
        key = self._key(user_id)
        data = json.dumps(event.to_ws_message())

        # Push to right (FIFO - pop from left)
        length = await self.redis.rpush(key, data)

        # Trim if too long (keep newest)
        if length > self.MAX_QUEUE_SIZE:
            await self.redis.ltrim(key, -self.MAX_QUEUE_SIZE, -1)
            length = self.MAX_QUEUE_SIZE

        # Refresh TTL
        await self.redis.expire(key, self.ttl)

        return length

    async def pop(self, user_id: str) -> Optional[dict]:
        """
        Pop oldest event from queue (non-blocking).

        Args:
            user_id: User identifier

        Returns:
            Event dict or None if queue is empty
        """
        key = self._key(user_id)
        data = await self.redis.lpop(key)

        if not data:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    async def pop_blocking(
        self,
        user_id: str,
        timeout: int = 30,
    ) -> Optional[dict]:
        """
        Pop oldest event with blocking wait.

        Args:
            user_id: User identifier
            timeout: Maximum seconds to wait (0 = forever)

        Returns:
            Event dict or None if timeout
        """
        key = self._key(user_id)

        # BLPOP returns (key, value) tuple or None
        result = await self.redis.blpop(key, timeout=timeout)

        if not result:
            return None

        try:
            return json.loads(result[1])
        except (json.JSONDecodeError, IndexError):
            return None

    async def peek(self, user_id: str) -> Optional[dict]:
        """
        Peek at oldest event without removing it.

        Args:
            user_id: User identifier

        Returns:
            Event dict or None if queue is empty
        """
        key = self._key(user_id)
        data = await self.redis.lindex(key, 0)

        if not data:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    async def get_all(self, user_id: str) -> List[dict]:
        """
        Get all events in queue without removing them.

        Args:
            user_id: User identifier

        Returns:
            List of event dicts
        """
        key = self._key(user_id)
        items = await self.redis.lrange(key, 0, -1)

        events = []
        for item in items:
            try:
                events.append(json.loads(item))
            except json.JSONDecodeError:
                continue

        return events

    async def length(self, user_id: str) -> int:
        """
        Get queue length.

        Args:
            user_id: User identifier

        Returns:
            Number of events in queue
        """
        key = self._key(user_id)
        return await self.redis.llen(key)

    async def clear(self, user_id: str) -> bool:
        """
        Clear user's queue.

        Args:
            user_id: User identifier

        Returns:
            True if queue existed and was cleared
        """
        key = self._key(user_id)
        result = await self.redis.delete(key)
        return result > 0

    async def push_to_all(
        self,
        user_ids: List[str],
        event: AnomalyEvent,
    ) -> int:
        """
        Push event to multiple users' queues.

        Args:
            user_ids: List of user identifiers
            event: AnomalyEvent to queue

        Returns:
            Number of users event was pushed to
        """
        if not user_ids:
            return 0

        data = json.dumps(event.to_ws_message())
        count = 0

        # Use pipeline for efficiency
        async with self.redis.pipeline() as pipe:
            for user_id in user_ids:
                key = self._key(user_id)
                pipe.rpush(key, data)
                pipe.expire(key, self.ttl)

            results = await pipe.execute()

        # Count successful pushes (every other result is from rpush)
        for i in range(0, len(results), 2):
            if results[i]:
                count += 1

        return count

    async def push_broadcast(
        self,
        event: AnomalyEvent,
        pattern: str = "*",
    ) -> int:
        """
        Push event to all active queues matching pattern.

        Warning: Uses KEYS command - avoid in high-load production.

        Args:
            event: AnomalyEvent to queue
            pattern: Queue key pattern (default: all)

        Returns:
            Number of queues event was pushed to
        """
        # Find all active queues
        search_pattern = f"{self.KEY_PREFIX}{pattern}"
        keys = await self.redis.keys(search_pattern)

        if not keys:
            return 0

        # Extract user IDs from keys
        user_ids = [
            key.replace(self.KEY_PREFIX, "")
            for key in keys
        ]

        return await self.push_to_all(user_ids, event)

    async def get_active_users(self) -> List[str]:
        """
        Get list of users with active queues.

        Warning: Uses KEYS command - avoid in high-load production.

        Returns:
            List of user IDs with queues
        """
        pattern = f"{self.KEY_PREFIX}*"
        keys = await self.redis.keys(pattern)

        return [
            key.replace(self.KEY_PREFIX, "")
            for key in keys
        ]


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Tracks which users are currently connected via WebSocket.
    Used for targeting anomalies to online users only.
    """

    KEY = "ritual_connections"
    HEARTBEAT_TTL = 60  # Connection expires after 60s without heartbeat

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def connect(self, user_id: str) -> None:
        """Register user connection."""
        await self.redis.hset(self.KEY, user_id, "1")

    async def disconnect(self, user_id: str) -> None:
        """Unregister user connection."""
        await self.redis.hdel(self.KEY, user_id)

    async def heartbeat(self, user_id: str) -> None:
        """Update connection heartbeat."""
        # Using hash for simplicity - could use sorted set with timestamps
        await self.redis.hset(self.KEY, user_id, "1")

    async def is_connected(self, user_id: str) -> bool:
        """Check if user is connected."""
        return await self.redis.hexists(self.KEY, user_id)

    async def get_connected_users(self) -> List[str]:
        """Get all connected user IDs."""
        users = await self.redis.hkeys(self.KEY)
        return list(users)

    async def get_connection_count(self) -> int:
        """Get number of active connections."""
        return await self.redis.hlen(self.KEY)

    async def clear_all(self) -> None:
        """Clear all connections (for shutdown)."""
        await self.redis.delete(self.KEY)
