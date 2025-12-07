"""
Integration tests for AnomalyQueue with FakeRedis.
TDD: Testing Redis queue operations.
"""
import pytest
import asyncio

from app.services.anomaly_queue import AnomalyQueue, ConnectionManager
from app.schemas.anomaly import AnomalyEvent, AnomalyType, AnomalySeverity


@pytest.mark.integration
class TestPushAndPop:
    """Tests for basic queue operations."""

    @pytest.mark.asyncio
    async def test_push_increases_queue_length(self, anomaly_queue):
        """Push should increase queue length."""
        # Arrange
        user_id = "queue-length"
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)

        # Act
        length = await anomaly_queue.push(user_id, event)

        # Assert
        assert length == 1

    @pytest.mark.asyncio
    async def test_pop_returns_oldest_first(self, anomaly_queue):
        """Pop should return events in FIFO order."""
        # Arrange
        user_id = "fifo-test"
        event1 = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        event2 = AnomalyEvent(type=AnomalyType.WHISPER, severity=AnomalySeverity.MODERATE)
        await anomaly_queue.push(user_id, event1)
        await anomaly_queue.push(user_id, event2)

        # Act
        popped1 = await anomaly_queue.pop(user_id)
        popped2 = await anomaly_queue.pop(user_id)

        # Assert
        assert popped1["payload"]["anomaly_type"] == "glitch"
        assert popped2["payload"]["anomaly_type"] == "whisper"

    @pytest.mark.asyncio
    async def test_pop_empty_returns_none(self, anomaly_queue):
        """Pop from empty queue should return None."""
        # Act
        result = await anomaly_queue.pop("empty-queue")

        # Assert
        assert result is None


@pytest.mark.integration
class TestPopBlocking:
    """Tests for blocking pop operations."""

    @pytest.mark.asyncio
    async def test_pop_blocking_returns_immediately_if_data(self, anomaly_queue):
        """Blocking pop should return immediately if data exists."""
        # Arrange
        user_id = "blocking-immediate"
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        await anomaly_queue.push(user_id, event)

        # Act
        result = await anomaly_queue.pop_blocking(user_id, timeout=1)

        # Assert
        assert result is not None
        assert result["payload"]["anomaly_type"] == "glitch"

    @pytest.mark.asyncio
    async def test_pop_blocking_times_out(self, anomaly_queue):
        """Blocking pop should return None after timeout."""
        # Act
        result = await anomaly_queue.pop_blocking("timeout-test", timeout=1)

        # Assert
        assert result is None


@pytest.mark.integration
class TestQueueManagement:
    """Tests for queue management operations."""

    @pytest.mark.asyncio
    async def test_length_returns_correct_count(self, anomaly_queue):
        """Length should return correct queue size."""
        # Arrange
        user_id = "length-test"
        for i in range(5):
            event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
            await anomaly_queue.push(user_id, event)

        # Act
        length = await anomaly_queue.length(user_id)

        # Assert
        assert length == 5

    @pytest.mark.asyncio
    async def test_clear_removes_all_events(self, anomaly_queue):
        """Clear should remove all events from queue."""
        # Arrange
        user_id = "clear-test"
        for i in range(3):
            event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
            await anomaly_queue.push(user_id, event)

        # Act
        result = await anomaly_queue.clear(user_id)

        # Assert
        assert result is True
        assert await anomaly_queue.length(user_id) == 0

    @pytest.mark.asyncio
    async def test_peek_does_not_remove(self, anomaly_queue):
        """Peek should return event without removing it."""
        # Arrange
        user_id = "peek-test"
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        await anomaly_queue.push(user_id, event)

        # Act
        peeked = await anomaly_queue.peek(user_id)
        length_after = await anomaly_queue.length(user_id)

        # Assert
        assert peeked is not None
        assert length_after == 1


@pytest.mark.integration
class TestQueueSizeLimit:
    """Tests for queue size limiting."""

    @pytest.mark.asyncio
    async def test_queue_trimmed_at_max_size(self, anomaly_queue):
        """Queue should be trimmed when exceeding MAX_QUEUE_SIZE."""
        # Arrange
        user_id = "trim-test"
        # Push more than MAX_QUEUE_SIZE (100)
        for i in range(110):
            event = AnomalyEvent(
                type=AnomalyType.GLITCH,
                severity=AnomalySeverity.MILD,
                data={"index": i},
            )
            await anomaly_queue.push(user_id, event)

        # Act
        length = await anomaly_queue.length(user_id)

        # Assert
        assert length == 100  # Trimmed to MAX_QUEUE_SIZE


@pytest.mark.integration
class TestPushToAll:
    """Tests for broadcasting to multiple users."""

    @pytest.mark.asyncio
    async def test_push_to_all_sends_to_multiple(self, anomaly_queue):
        """Should push event to all specified users."""
        # Arrange
        user_ids = ["user1", "user2", "user3"]
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)

        # Act
        count = await anomaly_queue.push_to_all(user_ids, event)

        # Assert
        assert count == 3
        for user_id in user_ids:
            assert await anomaly_queue.length(user_id) == 1


@pytest.mark.integration
class TestConnectionManager:
    """Tests for ConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect_registers_user(self, connection_manager):
        """Connect should register user."""
        # Act
        await connection_manager.connect("user1")

        # Assert
        assert await connection_manager.is_connected("user1") is True

    @pytest.mark.asyncio
    async def test_disconnect_unregisters_user(self, connection_manager):
        """Disconnect should unregister user."""
        # Arrange
        await connection_manager.connect("user1")

        # Act
        await connection_manager.disconnect("user1")

        # Assert
        assert await connection_manager.is_connected("user1") is False

    @pytest.mark.asyncio
    async def test_get_connected_users(self, connection_manager):
        """Should return list of connected users."""
        # Arrange
        await connection_manager.connect("user1")
        await connection_manager.connect("user2")

        # Act
        users = await connection_manager.get_connected_users()

        # Assert
        assert set(users) == {"user1", "user2"}

    @pytest.mark.asyncio
    async def test_get_connection_count(self, connection_manager):
        """Should return correct count of connections."""
        # Arrange
        await connection_manager.connect("user1")
        await connection_manager.connect("user2")
        await connection_manager.connect("user3")

        # Act
        count = await connection_manager.get_connection_count()

        # Assert
        assert count == 3


@pytest.mark.integration
class TestGetAll:
    """Tests for get_all method."""

    @pytest.mark.asyncio
    async def test_get_all_returns_all_events(self, anomaly_queue):
        """Should return all events without removing them."""
        # Arrange
        user_id = "get-all-test"
        event1 = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        event2 = AnomalyEvent(type=AnomalyType.WHISPER, severity=AnomalySeverity.MODERATE)
        event3 = AnomalyEvent(type=AnomalyType.SHADOW, severity=AnomalySeverity.EXTREME)
        await anomaly_queue.push(user_id, event1)
        await anomaly_queue.push(user_id, event2)
        await anomaly_queue.push(user_id, event3)

        # Act
        events = await anomaly_queue.get_all(user_id)

        # Assert
        assert len(events) == 3
        assert events[0]["payload"]["anomaly_type"] == "glitch"
        assert events[1]["payload"]["anomaly_type"] == "whisper"
        assert events[2]["payload"]["anomaly_type"] == "shadow"

    @pytest.mark.asyncio
    async def test_get_all_does_not_remove_events(self, anomaly_queue):
        """Should not remove events from queue."""
        # Arrange
        user_id = "get-all-peek"
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        await anomaly_queue.push(user_id, event)

        # Act
        events = await anomaly_queue.get_all(user_id)
        length_after = await anomaly_queue.length(user_id)

        # Assert
        assert len(events) == 1
        assert length_after == 1

    @pytest.mark.asyncio
    async def test_get_all_empty_queue(self, anomaly_queue):
        """Should return empty list for empty queue."""
        # Act
        events = await anomaly_queue.get_all("empty-queue")

        # Assert
        assert events == []

    @pytest.mark.asyncio
    async def test_get_all_handles_corrupted_entries(self, anomaly_queue):
        """Should skip corrupted JSON entries."""
        # Arrange
        user_id = "corrupted-entries"
        key = anomaly_queue._key(user_id)
        # Push valid event
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        await anomaly_queue.push(user_id, event)
        # Insert corrupted entry
        await anomaly_queue.redis.rpush(key, "not-valid-json")
        # Push another valid event
        await anomaly_queue.push(user_id, event)

        # Act
        events = await anomaly_queue.get_all(user_id)

        # Assert - should get 2 valid events, skip corrupted one
        assert len(events) == 2


@pytest.mark.integration
class TestPushBroadcast:
    """Tests for push_broadcast method."""

    @pytest.mark.asyncio
    async def test_push_broadcast_to_all_queues(self, anomaly_queue):
        """Should push event to all active queues."""
        # Arrange
        user_ids = ["user1", "user2", "user3"]
        # Create queues by pushing initial events
        for user_id in user_ids:
            await anomaly_queue.push(
                user_id,
                AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
            )

        # Act
        broadcast_event = AnomalyEvent(type=AnomalyType.WHISPER, severity=AnomalySeverity.MODERATE)
        count = await anomaly_queue.push_broadcast(broadcast_event)

        # Assert
        assert count == 3
        for user_id in user_ids:
            length = await anomaly_queue.length(user_id)
            assert length == 2  # Initial + broadcast

    @pytest.mark.asyncio
    async def test_push_broadcast_with_pattern(self, anomaly_queue):
        """Should push to queues matching pattern."""
        # Arrange
        # Create queues with different prefixes
        await anomaly_queue.push("admin-1", AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD))
        await anomaly_queue.push("admin-2", AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD))
        await anomaly_queue.push("user-1", AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD))

        # Act - broadcast only to admin queues
        event = AnomalyEvent(type=AnomalyType.WHISPER, severity=AnomalySeverity.MODERATE)
        count = await anomaly_queue.push_broadcast(event, pattern="admin-*")

        # Assert
        assert count == 2
        assert await anomaly_queue.length("admin-1") == 2
        assert await anomaly_queue.length("admin-2") == 2
        assert await anomaly_queue.length("user-1") == 1  # Not affected

    @pytest.mark.asyncio
    async def test_push_broadcast_no_active_queues(self, anomaly_queue):
        """Should return 0 when no active queues."""
        # Act
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        count = await anomaly_queue.push_broadcast(event)

        # Assert
        assert count == 0


@pytest.mark.integration
class TestGetActiveUsers:
    """Tests for get_active_users method."""

    @pytest.mark.asyncio
    async def test_get_active_users_empty(self, anomaly_queue):
        """Should return empty list when no active queues."""
        # Act
        users = await anomaly_queue.get_active_users()

        # Assert
        assert users == []

    @pytest.mark.asyncio
    async def test_get_active_users_multiple(self, anomaly_queue):
        """Should return all users with active queues."""
        # Arrange
        user_ids = ["user1", "user2", "user3"]
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        for user_id in user_ids:
            await anomaly_queue.push(user_id, event)

        # Act
        active_users = await anomaly_queue.get_active_users()

        # Assert
        assert set(active_users) == set(user_ids)


@pytest.mark.integration
class TestQueueEdgeCases:
    """Edge case tests for queue operations."""

    @pytest.mark.asyncio
    async def test_pop_corrupted_event_returns_none(self, anomaly_queue):
        """Should return None when popping corrupted event."""
        # Arrange
        user_id = "corrupted-pop"
        key = anomaly_queue._key(user_id)
        await anomaly_queue.redis.rpush(key, "not-valid-json")

        # Act
        result = await anomaly_queue.pop(user_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_peek_corrupted_event_returns_none(self, anomaly_queue):
        """Should return None when peeking corrupted event."""
        # Arrange
        user_id = "corrupted-peek"
        key = anomaly_queue._key(user_id)
        await anomaly_queue.redis.rpush(key, "not-valid-json")

        # Act
        result = await anomaly_queue.peek(user_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_push_to_all_empty_list(self, anomaly_queue):
        """Should return 0 when pushing to empty user list."""
        # Arrange
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)

        # Act
        count = await anomaly_queue.push_to_all([], event)

        # Assert
        assert count == 0

    @pytest.mark.asyncio
    async def test_multiple_pops_empty_queue(self, anomaly_queue):
        """Should handle multiple pops from empty queue."""
        # Act
        result1 = await anomaly_queue.pop("empty")
        result2 = await anomaly_queue.pop("empty")
        result3 = await anomaly_queue.pop("empty")

        # Assert
        assert result1 is None
        assert result2 is None
        assert result3 is None

    @pytest.mark.asyncio
    async def test_clear_nonexistent_queue(self, anomaly_queue):
        """Should return False when clearing nonexistent queue."""
        # Act
        result = await anomaly_queue.clear("nonexistent")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_queue_maintains_order_with_many_events(self, anomaly_queue):
        """Should maintain FIFO order with many events."""
        # Arrange
        user_id = "order-test"
        event_types = [AnomalyType.GLITCH, AnomalyType.WHISPER, AnomalyType.SHADOW,
                      AnomalyType.EYES, AnomalyType.STATIC]

        for i, event_type in enumerate(event_types):
            event = AnomalyEvent(
                type=event_type,
                severity=AnomalySeverity.MILD,
                data={"index": i}
            )
            await anomaly_queue.push(user_id, event)

        # Act - pop all
        popped = []
        for _ in range(len(event_types)):
            result = await anomaly_queue.pop(user_id)
            if result:
                popped.append(result["payload"]["anomaly_type"])

        # Assert
        expected = [t.value for t in event_types]
        assert popped == expected


@pytest.mark.integration
class TestConnectionManagerEdgeCases:
    """Edge case tests for ConnectionManager."""

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_user(self, connection_manager):
        """Should handle disconnecting nonexistent user."""
        # Act - should not raise error
        await connection_manager.disconnect("nonexistent")

        # Assert
        result = await connection_manager.is_connected("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_heartbeat_updates_connection(self, connection_manager):
        """Should update connection on heartbeat."""
        # Arrange
        await connection_manager.connect("user1")

        # Act
        await connection_manager.heartbeat("user1")

        # Assert
        result = await connection_manager.is_connected("user1")
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_all_removes_all_connections(self, connection_manager):
        """Should remove all connections."""
        # Arrange
        await connection_manager.connect("user1")
        await connection_manager.connect("user2")
        await connection_manager.connect("user3")

        # Act
        await connection_manager.clear_all()

        # Assert
        count = await connection_manager.get_connection_count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_connected_users_empty(self, connection_manager):
        """Should return empty list when no connections."""
        # Act
        users = await connection_manager.get_connected_users()

        # Assert
        assert users == []

    @pytest.mark.asyncio
    async def test_multiple_connects_same_user(self, connection_manager):
        """Should handle multiple connects for same user."""
        # Act
        await connection_manager.connect("user1")
        await connection_manager.connect("user1")
        await connection_manager.connect("user1")

        # Assert
        count = await connection_manager.get_connection_count()
        assert count == 1  # Only one entry

    @pytest.mark.asyncio
    async def test_connect_then_disconnect_then_reconnect(self, connection_manager):
        """Should handle reconnection after disconnect."""
        # Arrange
        await connection_manager.connect("user1")
        await connection_manager.disconnect("user1")

        # Act
        await connection_manager.connect("user1")

        # Assert
        result = await connection_manager.is_connected("user1")
        assert result is True


@pytest.mark.integration
class TestQueueTTLBehavior:
    """Tests for queue TTL behavior."""

    @pytest.mark.asyncio
    async def test_push_refreshes_ttl(self, anomaly_queue):
        """Push should refresh queue TTL."""
        # Arrange
        user_id = "ttl-test"
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)

        # Act
        await anomaly_queue.push(user_id, event)
        key = anomaly_queue._key(user_id)
        ttl = await anomaly_queue.redis.ttl(key)

        # Assert
        assert ttl > 0  # TTL is set
        assert ttl <= anomaly_queue.ttl  # Within expected range

    @pytest.mark.asyncio
    async def test_multiple_pushes_maintain_ttl(self, anomaly_queue):
        """Multiple pushes should maintain TTL."""
        # Arrange
        user_id = "multi-push-ttl"
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)

        # Act
        for _ in range(5):
            await anomaly_queue.push(user_id, event)

        key = anomaly_queue._key(user_id)
        ttl = await anomaly_queue.redis.ttl(key)

        # Assert
        assert ttl > 0


@pytest.mark.integration
class TestPopBlockingEdgeCases:
    """Edge case tests for pop_blocking."""

    @pytest.mark.asyncio
    async def test_pop_blocking_with_corrupted_data(self, anomaly_queue):
        """Should return None for corrupted data in blocking pop."""
        # Arrange
        user_id = "blocking-corrupted"
        key = anomaly_queue._key(user_id)
        await anomaly_queue.redis.rpush(key, "not-valid-json")

        # Act
        result = await anomaly_queue.pop_blocking(user_id, timeout=1)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_pop_blocking_zero_timeout(self, anomaly_queue):
        """Should wait indefinitely with timeout=0 (but we'll push data)."""
        # Arrange
        user_id = "blocking-zero"
        event = AnomalyEvent(type=AnomalyType.GLITCH, severity=AnomalySeverity.MILD)
        await anomaly_queue.push(user_id, event)

        # Act - should return immediately since data exists
        result = await anomaly_queue.pop_blocking(user_id, timeout=0)

        # Assert
        assert result is not None
        assert result["payload"]["anomaly_type"] == "glitch"
