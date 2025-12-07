"""
Unit tests for Redis client utilities.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.core import redis as redis_module


class TestGetRedis:
    """Tests for get_redis() dependency."""

    @pytest.mark.asyncio
    async def test_raises_when_not_initialized(self):
        """Should raise RuntimeError if Redis not initialized."""
        # Ensure client is None
        original = redis_module._redis_client
        redis_module._redis_client = None

        with pytest.raises(RuntimeError, match="not initialized"):
            await redis_module.get_redis()

        redis_module._redis_client = original

    @pytest.mark.asyncio
    async def test_returns_client_when_initialized(self):
        """Should return client when initialized."""
        mock_client = MagicMock()
        original = redis_module._redis_client
        redis_module._redis_client = mock_client

        result = await redis_module.get_redis()
        assert result is mock_client

        redis_module._redis_client = original


class TestGetRedisSync:
    """Tests for get_redis_sync()."""

    def test_returns_none_when_not_initialized(self):
        """Should return None if not initialized."""
        original = redis_module._redis_client
        redis_module._redis_client = None

        result = redis_module.get_redis_sync()
        assert result is None

        redis_module._redis_client = original

    def test_returns_client_when_initialized(self):
        """Should return client when initialized."""
        mock_client = MagicMock()
        original = redis_module._redis_client
        redis_module._redis_client = mock_client

        result = redis_module.get_redis_sync()
        assert result is mock_client

        redis_module._redis_client = original


class TestInitRedis:
    """Tests for init_redis()."""

    @pytest.mark.asyncio
    @patch('app.core.redis.ConnectionPool')
    @patch('app.core.redis.redis.Redis')
    async def test_creates_pool_and_client(self, mock_redis_class, mock_pool_class):
        """Should create connection pool and client."""
        mock_pool = MagicMock()
        mock_pool_class.from_url.return_value = mock_pool

        mock_client = AsyncMock()
        mock_redis_class.return_value = mock_client

        result = await redis_module.init_redis()

        mock_pool_class.from_url.assert_called_once()
        mock_client.ping.assert_awaited_once()


class TestCloseRedis:
    """Tests for close_redis()."""

    @pytest.mark.asyncio
    async def test_closes_client_and_pool(self):
        """Should close client and disconnect pool."""
        mock_client = AsyncMock()
        mock_pool = AsyncMock()

        redis_module._redis_client = mock_client
        redis_module._redis_pool = mock_pool

        await redis_module.close_redis()

        mock_client.close.assert_awaited_once()
        mock_pool.disconnect.assert_awaited_once()

        assert redis_module._redis_client is None
        assert redis_module._redis_pool is None
