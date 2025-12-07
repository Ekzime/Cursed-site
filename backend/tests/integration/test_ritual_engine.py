"""
Integration tests for RitualEngine.
TDD: Testing full engine flow with FakeRedis.
"""
import pytest
from unittest.mock import patch

from app.services.ritual_engine import RitualEngine
from app.schemas.anomaly import AnomalyType


@pytest.mark.integration
class TestOnRequest:
    """Tests for RitualEngine.on_request() method."""

    @pytest.mark.asyncio
    async def test_creates_state_for_new_user(self, ritual_engine):
        """Should create state for new user."""
        # Arrange
        user_id = "new-visitor"

        # Act
        state, is_new = await ritual_engine.on_request(user_id)

        # Assert
        assert is_new is True
        assert state.user_id == user_id
        # Note: progress is 5 because first_visit trigger adds +5
        assert state.progress == 5
        assert "first_visit" in state.triggers_hit

    @pytest.mark.asyncio
    async def test_returns_existing_state(self, ritual_engine):
        """Should return existing state for known user."""
        # Arrange
        user_id = "returning-visitor"
        await ritual_engine.on_request(user_id)  # First visit

        # Act
        state, is_new = await ritual_engine.on_request(user_id)

        # Assert
        assert is_new is False

    @pytest.mark.asyncio
    @patch('app.services.triggers.is_night_hour')
    @patch('app.services.triggers.is_witching_hour')
    async def test_checks_triggers_on_request(
        self, mock_witching, mock_night, ritual_engine
    ):
        """Should check triggers and update state."""
        # Arrange
        mock_night.return_value = False
        mock_witching.return_value = False
        user_id = "trigger-test"

        # Act
        state, _ = await ritual_engine.on_request(user_id)

        # Assert
        # First visit trigger should fire
        assert "first_visit" in state.triggers_hit


@pytest.mark.integration
class TestOnThreadView:
    """Tests for RitualEngine.on_thread_view() method."""

    @pytest.mark.asyncio
    async def test_adds_thread_to_viewed(self, ritual_engine):
        """Should add thread to viewed list."""
        # Arrange
        user_id = "thread-viewer"
        await ritual_engine.on_request(user_id)

        # Act
        state = await ritual_engine.on_thread_view(user_id, thread_id=123)

        # Assert
        assert 123 in state.viewed_threads

    @pytest.mark.asyncio
    async def test_increases_progress(self, ritual_engine):
        """Should increase progress on first view."""
        # Arrange
        user_id = "progress-increase"
        state, _ = await ritual_engine.on_request(user_id)
        initial_progress = state.progress

        # Act
        state = await ritual_engine.on_thread_view(user_id, thread_id=1)

        # Assert
        assert state.progress >= initial_progress


@pytest.mark.integration
class TestQueueAnomaly:
    """Tests for anomaly queueing."""

    @pytest.mark.asyncio
    async def test_queue_anomaly_for_type(self, ritual_engine):
        """Should generate and queue specific anomaly type."""
        # Arrange
        user_id = "anomaly-queue"
        await ritual_engine.on_request(user_id)

        # Act
        event = await ritual_engine.queue_anomaly_for_type(
            user_id,
            AnomalyType.WHISPER,
            custom_data={"message": "test"}
        )

        # Assert
        assert event is not None
        assert event.type == AnomalyType.WHISPER

    @pytest.mark.asyncio
    async def test_queue_anomaly_returns_none_for_unknown_user(self, ritual_engine):
        """Should return None if user state doesn't exist."""
        # Act
        event = await ritual_engine.queue_anomaly_for_type(
            "nonexistent",
            AnomalyType.GLITCH,
        )

        # Assert
        assert event is None


@pytest.mark.integration
class TestMutations:
    """Tests for content mutation."""

    @pytest.mark.asyncio
    async def test_mutate_post_returns_dict(self, ritual_engine):
        """Should return mutated post dict."""
        # Arrange
        user_id = "mutate-test"
        await ritual_engine.on_request(user_id)
        state = await ritual_engine.get_user_state(user_id)
        post = {"id": 1, "content": "Test content", "thread_id": 1}

        # Act
        result = ritual_engine.mutate_post(post, state)

        # Assert
        assert isinstance(result, dict)
        assert "content" in result

    @pytest.mark.asyncio
    async def test_mutate_posts_list(self, ritual_engine):
        """Should mutate list of posts."""
        # Arrange
        user_id = "mutate-list"
        await ritual_engine.on_request(user_id)
        state = await ritual_engine.get_user_state(user_id)
        posts = [
            {"id": 1, "content": "Post 1", "thread_id": 1},
            {"id": 2, "content": "Post 2", "thread_id": 1},
        ]

        # Act
        results = ritual_engine.mutate_posts_list(posts, state)

        # Assert
        assert len(results) == 2


@pytest.mark.integration
class TestStateManagement:
    """Tests for state management methods."""

    @pytest.mark.asyncio
    async def test_reset_user_state(self, ritual_engine):
        """Should reset user state to initial values."""
        # Arrange
        user_id = "reset-test"
        state, _ = await ritual_engine.on_request(user_id)
        await ritual_engine.set_user_progress(user_id, 50)

        # Act
        new_state = await ritual_engine.reset_user_state(user_id)

        # Assert
        assert new_state.progress == 0
        assert len(new_state.triggers_hit) == 0

    @pytest.mark.asyncio
    async def test_set_user_progress(self, ritual_engine):
        """Should set progress to specific value."""
        # Arrange
        user_id = "set-progress"
        await ritual_engine.on_request(user_id)

        # Act
        state = await ritual_engine.set_user_progress(user_id, 75)

        # Assert
        assert state.progress == 75

    @pytest.mark.asyncio
    async def test_get_connected_users(self, ritual_engine):
        """Should return list of connected users."""
        # Arrange - connect some users via connection_manager
        await ritual_engine.connection_manager.connect("user1")
        await ritual_engine.connection_manager.connect("user2")

        # Act
        users = await ritual_engine.get_connected_users()

        # Assert
        assert set(users) == {"user1", "user2"}
