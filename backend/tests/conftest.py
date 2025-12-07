"""
Shared pytest fixtures for Cursed Board tests.
"""
import os

# Set test environment variables BEFORE any app imports
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_USER", "test")
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("DATABASE_NAME", "test_db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

import fakeredis.aioredis

from app.schemas.ritual import RitualState
from app.services.ritual_state import RitualStateManager
from app.services.progress_engine import ProgressEngine
from app.services.triggers import TriggerChecker
from app.services.anomaly_generator import AnomalyGenerator
from app.services.anomaly_queue import AnomalyQueue, ConnectionManager
from app.services.content_mutator import ContentMutator
from app.services.ritual_engine import RitualEngine


# =============================================================================
# TestClient Fixture
# =============================================================================

@pytest.fixture
def test_client():
    """TestClient for API integration tests."""
    from unittest.mock import patch, AsyncMock
    from fastapi.testclient import TestClient
    from main import app
    from app.core.redis import get_redis

    # Create a mock Redis client
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    # Create mock RitualState
    mock_state = RitualState(
        user_id="test-user",
        progress=0,
        viewed_threads=[],
        viewed_posts=[],
        time_on_site=0,
        first_visit=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        triggers_hit=set(),
        known_patterns={},
    )

    # Create mock state manager
    mock_state_manager = AsyncMock()
    mock_state_manager.get_or_create = AsyncMock(return_value=(mock_state, False))
    mock_state_manager.save = AsyncMock(return_value=True)

    # Override get_redis dependency
    async def mock_get_redis():
        return mock_redis

    # Override lifespan to skip database and Redis initialization
    @asynccontextmanager
    async def test_lifespan(app):
        """Minimal lifespan for testing."""
        app.state.redis = mock_redis
        yield

    # Apply test lifespan
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan

    # Override get_redis dependency
    app.dependency_overrides[get_redis] = mock_get_redis

    # Patch RitualStateManager in the middleware module
    with patch(
        "app.middleware.ritual_middleware.RitualStateManager",
        return_value=mock_state_manager
    ):
        with TestClient(app) as client:
            yield client

    # Restore original lifespan and clear dependency overrides
    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()


# =============================================================================
# Redis Fixtures
# =============================================================================

@pytest.fixture
async def redis_client():
    """FakeRedis client for integration tests."""
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


# =============================================================================
# Service Fixtures
# =============================================================================

@pytest.fixture
def progress_engine():
    """ProgressEngine instance for unit tests."""
    return ProgressEngine()


@pytest.fixture
def trigger_checker():
    """TriggerChecker instance for unit tests."""
    return TriggerChecker()


@pytest.fixture
def anomaly_generator():
    """AnomalyGenerator instance for unit tests."""
    return AnomalyGenerator()


@pytest.fixture
def content_mutator():
    """ContentMutator instance for unit tests."""
    return ContentMutator()


@pytest.fixture
async def state_manager(redis_client):
    """RitualStateManager with FakeRedis."""
    return RitualStateManager(redis_client)


@pytest.fixture
async def anomaly_queue(redis_client):
    """AnomalyQueue with FakeRedis."""
    return AnomalyQueue(redis_client)


@pytest.fixture
async def connection_manager(redis_client):
    """ConnectionManager with FakeRedis."""
    return ConnectionManager(redis_client)


@pytest.fixture
async def ritual_engine(redis_client):
    """Full RitualEngine with FakeRedis."""
    return RitualEngine(redis_client)


# =============================================================================
# State Fixtures
# =============================================================================

@pytest.fixture
def new_user_state():
    """Fresh RitualState for new user."""
    return RitualState(
        user_id="test-user-new",
        progress=0,
        viewed_threads=[],
        viewed_posts=[],
        time_on_site=0,
        first_visit=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        triggers_hit=set(),
        known_patterns={},
    )


@pytest.fixture
def medium_progress_state():
    """RitualState at MEDIUM level (progress=35)."""
    return RitualState(
        user_id="test-user-medium",
        progress=35,
        viewed_threads=[1, 2, 3, 4, 5],
        viewed_posts=list(range(1, 26)),  # 25 posts
        time_on_site=1800,  # 30 minutes
        first_visit=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        triggers_hit={"first_visit", "deep_reader"},
        known_patterns={"reading_style": "careful"},
    )


@pytest.fixture
def critical_progress_state():
    """RitualState at CRITICAL level (progress=90)."""
    return RitualState(
        user_id="test-user-critical",
        progress=90,
        viewed_threads=list(range(1, 51)),  # 50 threads
        viewed_posts=list(range(1, 201)),   # 200 posts
        time_on_site=7200,  # 2 hours
        first_visit=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        triggers_hit={"first_visit", "deep_reader", "halfway", "almost_there"},
        known_patterns={"reading_style": "obsessive", "seeking": True},
    )
