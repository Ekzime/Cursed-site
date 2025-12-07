"""
Integration tests for RitualStateManager with FakeRedis.
TDD: Testing Redis CRUD operations.
"""
import pytest
from datetime import datetime

from app.services.ritual_state import RitualStateManager
from app.schemas.ritual import RitualState


@pytest.mark.integration
class TestGetOrCreate:
    """Tests for RitualStateManager.get_or_create() method."""

    @pytest.mark.asyncio
    async def test_creates_new_user_state(self, state_manager):
        """Should create new state for unknown user."""
        # Arrange
        user_id = "new-user-123"

        # Act
        state, is_new = await state_manager.get_or_create(user_id)

        # Assert
        assert is_new is True
        assert state.user_id == user_id
        assert state.progress == 0

    @pytest.mark.asyncio
    async def test_returns_existing_state(self, state_manager):
        """Should return existing state without creating new."""
        # Arrange
        user_id = "existing-user"
        state1, _ = await state_manager.get_or_create(user_id)
        state1.progress = 50
        await state_manager.save(state1)

        # Act
        state2, is_new = await state_manager.get_or_create(user_id)

        # Assert
        assert is_new is False
        assert state2.progress == 50


@pytest.mark.integration
class TestSaveAndRetrieve:
    """Tests for save and retrieval operations."""

    @pytest.mark.asyncio
    async def test_save_persists_state(self, state_manager):
        """Saved state should be retrievable."""
        # Arrange
        user_id = "persist-test"
        state = RitualState(user_id=user_id, progress=75)

        # Act
        await state_manager.save(state)
        retrieved = await state_manager.get(user_id)

        # Assert
        assert retrieved is not None
        assert retrieved.progress == 75

    @pytest.mark.asyncio
    async def test_save_updates_last_activity(self, state_manager):
        """Save should update last_activity timestamp."""
        # Arrange
        user_id = "activity-test"
        state = RitualState(user_id=user_id)
        original_activity = state.last_activity

        # Act
        await state_manager.save(state)
        retrieved = await state_manager.get(user_id)

        # Assert
        assert retrieved.last_activity >= original_activity


@pytest.mark.integration
class TestUpdateProgress:
    """Tests for progress update operations."""

    @pytest.mark.asyncio
    async def test_update_progress_positive(self, state_manager):
        """Should increase progress."""
        # Arrange
        user_id = "progress-pos"
        state, _ = await state_manager.get_or_create(user_id)
        state.progress = 50
        await state_manager.save(state)

        # Act
        updated = await state_manager.update_progress(user_id, delta=10)

        # Assert
        assert updated.progress == 60

    @pytest.mark.asyncio
    async def test_update_progress_negative(self, state_manager):
        """Should decrease progress."""
        # Arrange
        user_id = "progress-neg"
        state, _ = await state_manager.get_or_create(user_id)
        state.progress = 50
        await state_manager.save(state)

        # Act
        updated = await state_manager.update_progress(user_id, delta=-20)

        # Assert
        assert updated.progress == 30

    @pytest.mark.asyncio
    async def test_update_progress_clamps_to_zero(self, state_manager):
        """Progress should not go below 0."""
        # Arrange
        user_id = "progress-clamp-low"
        state, _ = await state_manager.get_or_create(user_id)
        state.progress = 5
        await state_manager.save(state)

        # Act
        updated = await state_manager.update_progress(user_id, delta=-50)

        # Assert
        assert updated.progress == 0

    @pytest.mark.asyncio
    async def test_update_progress_clamps_to_100(self, state_manager):
        """Progress should not exceed 100."""
        # Arrange
        user_id = "progress-clamp-high"
        state, _ = await state_manager.get_or_create(user_id)
        state.progress = 95
        await state_manager.save(state)

        # Act
        updated = await state_manager.update_progress(user_id, delta=50)

        # Assert
        assert updated.progress == 100


@pytest.mark.integration
class TestViewedContent:
    """Tests for viewed content tracking."""

    @pytest.mark.asyncio
    async def test_add_viewed_thread(self, state_manager):
        """Should add thread to viewed list."""
        # Arrange
        user_id = "viewed-thread"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        updated = await state_manager.add_viewed_thread(user_id, thread_id=123)

        # Assert
        assert 123 in updated.viewed_threads

    @pytest.mark.asyncio
    async def test_add_viewed_thread_no_duplicates(self, state_manager):
        """Should not add duplicate thread IDs."""
        # Arrange
        user_id = "no-dup-thread"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        await state_manager.add_viewed_thread(user_id, thread_id=123)
        await state_manager.add_viewed_thread(user_id, thread_id=123)
        updated = await state_manager.get(user_id)

        # Assert
        assert updated.viewed_threads.count(123) == 1

    @pytest.mark.asyncio
    async def test_viewed_threads_limit_100(self, state_manager):
        """Should keep only last 100 viewed threads."""
        # Arrange
        user_id = "limit-threads"
        state, _ = await state_manager.get_or_create(user_id)
        state.viewed_threads = list(range(1, 101))  # 100 threads
        await state_manager.save(state)

        # Act
        await state_manager.add_viewed_thread(user_id, thread_id=999)
        updated = await state_manager.get(user_id)

        # Assert
        assert len(updated.viewed_threads) == 100
        assert 999 in updated.viewed_threads
        assert 1 not in updated.viewed_threads  # Oldest removed


@pytest.mark.integration
class TestTriggers:
    """Tests for trigger tracking."""

    @pytest.mark.asyncio
    async def test_add_trigger(self, state_manager):
        """Should add trigger to triggers_hit set."""
        # Arrange
        user_id = "trigger-add"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        updated = await state_manager.add_trigger(user_id, "first_visit")

        # Assert
        assert "first_visit" in updated.triggers_hit

    @pytest.mark.asyncio
    async def test_add_trigger_idempotent(self, state_manager):
        """Adding same trigger twice should have no effect."""
        # Arrange
        user_id = "trigger-idem"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        await state_manager.add_trigger(user_id, "test_trigger")
        await state_manager.add_trigger(user_id, "test_trigger")
        updated = await state_manager.get(user_id)

        # Assert
        assert "test_trigger" in updated.triggers_hit
        # Set ensures no duplicates


@pytest.mark.integration
class TestDelete:
    """Tests for delete operations."""

    @pytest.mark.asyncio
    async def test_delete_removes_state(self, state_manager):
        """Delete should remove state from Redis."""
        # Arrange
        user_id = "delete-test"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        result = await state_manager.delete(user_id)

        # Assert
        assert result is True
        assert await state_manager.get(user_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, state_manager):
        """Delete of nonexistent state should return False."""
        # Act
        result = await state_manager.delete("nonexistent-user")

        # Assert
        assert result is False


@pytest.mark.integration
class TestExists:
    """Tests for existence checking."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing(self, state_manager):
        """Should return True for existing state."""
        # Arrange
        user_id = "exists-true"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        result = await state_manager.exists(user_id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_nonexistent(self, state_manager):
        """Should return False for nonexistent state."""
        # Act
        result = await state_manager.exists("nonexistent")

        # Assert
        assert result is False


@pytest.mark.integration
class TestSetProgress:
    """Tests for set_progress method."""

    @pytest.mark.asyncio
    async def test_set_progress_updates_value(self, state_manager):
        """Should set progress to specific value."""
        # Arrange
        user_id = "set-progress-test"
        state, _ = await state_manager.get_or_create(user_id)
        state.progress = 50
        await state_manager.save(state)

        # Act
        updated = await state_manager.set_progress(user_id, 75)

        # Assert
        assert updated is not None
        assert updated.progress == 75

    @pytest.mark.asyncio
    async def test_set_progress_clamps_to_zero(self, state_manager):
        """Should clamp negative progress to 0."""
        # Arrange
        user_id = "set-clamp-low"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        updated = await state_manager.set_progress(user_id, -10)

        # Assert
        assert updated.progress == 0

    @pytest.mark.asyncio
    async def test_set_progress_clamps_to_100(self, state_manager):
        """Should clamp progress over 100."""
        # Arrange
        user_id = "set-clamp-high"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        updated = await state_manager.set_progress(user_id, 150)

        # Assert
        assert updated.progress == 100

    @pytest.mark.asyncio
    async def test_set_progress_nonexistent_returns_none(self, state_manager):
        """Should return None for nonexistent user."""
        # Act
        result = await state_manager.set_progress("nonexistent", 50)

        # Assert
        assert result is None


@pytest.mark.integration
class TestAddViewedPost:
    """Tests for add_viewed_post method."""

    @pytest.mark.asyncio
    async def test_add_viewed_post(self, state_manager):
        """Should add post to viewed list."""
        # Arrange
        user_id = "viewed-post-test"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        updated = await state_manager.add_viewed_post(user_id, post_id=456)

        # Assert
        assert 456 in updated.viewed_posts

    @pytest.mark.asyncio
    async def test_add_viewed_post_no_duplicates(self, state_manager):
        """Should not add duplicate post IDs."""
        # Arrange
        user_id = "no-dup-post"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        await state_manager.add_viewed_post(user_id, post_id=456)
        await state_manager.add_viewed_post(user_id, post_id=456)
        updated = await state_manager.get(user_id)

        # Assert
        assert updated.viewed_posts.count(456) == 1

    @pytest.mark.asyncio
    async def test_viewed_posts_limit_500(self, state_manager):
        """Should keep only last 500 viewed posts."""
        # Arrange
        user_id = "limit-posts"
        state, _ = await state_manager.get_or_create(user_id)
        state.viewed_posts = list(range(1, 501))  # 500 posts
        await state_manager.save(state)

        # Act
        await state_manager.add_viewed_post(user_id, post_id=999)
        updated = await state_manager.get(user_id)

        # Assert
        assert len(updated.viewed_posts) == 500
        assert 999 in updated.viewed_posts
        assert 1 not in updated.viewed_posts  # Oldest removed

    @pytest.mark.asyncio
    async def test_add_viewed_post_nonexistent_returns_none(self, state_manager):
        """Should return None for nonexistent user."""
        # Act
        result = await state_manager.add_viewed_post("nonexistent", 123)

        # Assert
        assert result is None


@pytest.mark.integration
class TestAddTimeOnSite:
    """Tests for add_time_on_site method."""

    @pytest.mark.asyncio
    async def test_add_time_on_site(self, state_manager):
        """Should add seconds to time_on_site."""
        # Arrange
        user_id = "time-test"
        state, _ = await state_manager.get_or_create(user_id)
        state.time_on_site = 100
        await state_manager.save(state)

        # Act
        updated = await state_manager.add_time_on_site(user_id, 50)

        # Assert
        assert updated.time_on_site == 150

    @pytest.mark.asyncio
    async def test_add_time_on_site_from_zero(self, state_manager):
        """Should add time starting from zero."""
        # Arrange
        user_id = "time-zero"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        updated = await state_manager.add_time_on_site(user_id, 300)

        # Assert
        assert updated.time_on_site == 300

    @pytest.mark.asyncio
    async def test_add_time_on_site_nonexistent_returns_none(self, state_manager):
        """Should return None for nonexistent user."""
        # Act
        result = await state_manager.add_time_on_site("nonexistent", 100)

        # Assert
        assert result is None


@pytest.mark.integration
class TestUpdateKnownPatterns:
    """Tests for update_known_patterns method."""

    @pytest.mark.asyncio
    async def test_update_known_patterns_adds_new_key(self, state_manager):
        """Should add new key to known_patterns."""
        # Arrange
        user_id = "patterns-test"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        updated = await state_manager.update_known_patterns(user_id, "theme", "dark")

        # Assert
        assert updated.known_patterns["theme"] == "dark"

    @pytest.mark.asyncio
    async def test_update_known_patterns_updates_existing_key(self, state_manager):
        """Should update existing key in known_patterns."""
        # Arrange
        user_id = "patterns-update"
        state, _ = await state_manager.get_or_create(user_id)
        state.known_patterns = {"theme": "light"}
        await state_manager.save(state)

        # Act
        updated = await state_manager.update_known_patterns(user_id, "theme", "dark")

        # Assert
        assert updated.known_patterns["theme"] == "dark"

    @pytest.mark.asyncio
    async def test_update_known_patterns_preserves_other_keys(self, state_manager):
        """Should preserve other keys when updating."""
        # Arrange
        user_id = "patterns-preserve"
        state, _ = await state_manager.get_or_create(user_id)
        state.known_patterns = {"theme": "light", "lang": "en"}
        await state_manager.save(state)

        # Act
        updated = await state_manager.update_known_patterns(user_id, "theme", "dark")

        # Assert
        assert updated.known_patterns["theme"] == "dark"
        assert updated.known_patterns["lang"] == "en"

    @pytest.mark.asyncio
    async def test_update_known_patterns_nonexistent_returns_none(self, state_manager):
        """Should return None for nonexistent user."""
        # Act
        result = await state_manager.update_known_patterns("nonexistent", "key", "value")

        # Assert
        assert result is None


@pytest.mark.integration
class TestGetAllUserIds:
    """Tests for get_all_user_ids method."""

    @pytest.mark.asyncio
    async def test_get_all_user_ids_empty(self, state_manager):
        """Should return empty list when no users."""
        # Act
        user_ids = await state_manager.get_all_user_ids()

        # Assert
        assert user_ids == []

    @pytest.mark.asyncio
    async def test_get_all_user_ids_multiple_users(self, state_manager):
        """Should return all user IDs."""
        # Arrange
        await state_manager.get_or_create("user1")
        await state_manager.get_or_create("user2")
        await state_manager.get_or_create("user3")

        # Act
        user_ids = await state_manager.get_all_user_ids()

        # Assert
        assert set(user_ids) == {"user1", "user2", "user3"}


@pytest.mark.integration
class TestRefreshTTL:
    """Tests for refresh_ttl method."""

    @pytest.mark.asyncio
    async def test_refresh_ttl_existing_user(self, state_manager):
        """Should refresh TTL for existing user."""
        # Arrange
        user_id = "refresh-test"
        state, _ = await state_manager.get_or_create(user_id)
        await state_manager.save(state)

        # Act
        result = await state_manager.refresh_ttl(user_id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_refresh_ttl_nonexistent_user(self, state_manager):
        """Should return False for nonexistent user."""
        # Act
        result = await state_manager.refresh_ttl("nonexistent")

        # Assert
        assert result is False


@pytest.mark.integration
class TestCorruptedDataHandling:
    """Tests for handling corrupted Redis data."""

    @pytest.mark.asyncio
    async def test_get_with_corrupted_json(self, state_manager):
        """Should handle corrupted JSON gracefully."""
        # Arrange
        user_id = "corrupted-test"
        key = state_manager._key(user_id)
        # Insert invalid JSON
        await state_manager.redis.set(key, "not-valid-json")

        # Act
        result = await state_manager.get(user_id)

        # Assert
        assert result is None
        # Key should be deleted
        assert await state_manager.redis.exists(key) == 0

    @pytest.mark.asyncio
    async def test_get_with_invalid_state_data(self, state_manager):
        """Should handle invalid state structure."""
        # Arrange
        user_id = "invalid-test"
        key = state_manager._key(user_id)
        # Insert JSON with wrong structure
        await state_manager.redis.set(key, '{"invalid": "structure"}')

        # Act
        result = await state_manager.get(user_id)

        # Assert
        assert result is None


@pytest.mark.integration
class TestConcurrentOperations:
    """Tests for concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_progress_updates(self, state_manager):
        """Should handle concurrent progress updates."""
        # Arrange
        user_id = "concurrent-test"
        await state_manager.get_or_create(user_id)

        # Act - simulate concurrent updates
        import asyncio
        results = await asyncio.gather(
            state_manager.update_progress(user_id, 5),
            state_manager.update_progress(user_id, 5),
            state_manager.update_progress(user_id, 5),
        )

        # Assert - final state should have some progress
        final_state = await state_manager.get(user_id)
        assert final_state.progress >= 5  # At least one update succeeded

    @pytest.mark.asyncio
    async def test_concurrent_viewed_threads(self, state_manager):
        """Should handle concurrent viewed thread additions."""
        # Arrange
        user_id = "concurrent-threads"
        await state_manager.get_or_create(user_id)

        # Act
        import asyncio
        await asyncio.gather(
            state_manager.add_viewed_thread(user_id, 1),
            state_manager.add_viewed_thread(user_id, 2),
            state_manager.add_viewed_thread(user_id, 3),
        )

        # Assert
        final_state = await state_manager.get(user_id)
        assert len(final_state.viewed_threads) >= 1  # At least one succeeded
