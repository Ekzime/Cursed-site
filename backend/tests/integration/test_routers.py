"""
Integration tests for API routers.

Tests API endpoints with mocked dependencies to verify:
- Response structure and status codes
- Request validation
- Basic endpoint functionality
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status

from app.schemas.anomaly import AnomalyType, AnomalySeverity
from app.schemas.ritual import RitualState
from app.services.progress_engine import ProgressLevel
from datetime import datetime


class TestHealthAndRoot:
    """Tests for root and health check endpoints."""

    def test_root_endpoint(self, test_client):
        """Should return API running message."""
        response = test_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Cursed Board API" in data["message"]

    def test_health_check_with_redis(self, test_client):
        """Should return healthy status when Redis is connected."""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "redis" in data
        assert data["redis"] == "connected"
        assert data["status"] in ["healthy", "degraded"]


class TestRitualAdminRoutes:
    """Tests for /admin/ritual endpoints."""

    def test_get_anomaly_types(self, test_client):
        """Should return list of anomaly types and severities."""
        response = test_client.get("/admin/ritual/anomaly/types")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "types" in data
        assert "severities" in data

        # Verify all anomaly types are present
        expected_types = [t.value for t in AnomalyType]
        assert set(data["types"]) == set(expected_types)

        # Verify all severities are present
        expected_severities = [s.value for s in AnomalySeverity]
        assert set(data["severities"]) == set(expected_severities)

    def test_get_progress_levels(self, test_client):
        """Should return progress level information."""
        response = test_client.get("/admin/ritual/levels")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "levels" in data

        # Verify all progress levels are present
        levels = data["levels"]
        assert "low" in levels
        assert "medium" in levels
        assert "high" in levels
        assert "critical" in levels

        # Verify structure of level data
        for level_name, level_data in levels.items():
            assert "range" in level_data
            assert "description" in level_data
            assert isinstance(level_data["range"], str)
            assert isinstance(level_data["description"], str)

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_get_user_state_success(self, mock_engine_class, test_client):
        """Should return user state when it exists."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        # Create test state
        test_state = RitualState(
            user_id="test-user",
            progress=50,
            viewed_threads=[1, 2, 3],
            viewed_posts=[1, 2, 3, 4, 5],
            time_on_site=1800,
            first_visit=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            triggers_hit={"first_visit", "deep_reader"},
            known_patterns={"reading_style": "careful"},
        )

        mock_engine.get_user_state.return_value = test_state
        # progress_engine is sync, use MagicMock
        mock_engine.progress_engine = MagicMock()
        mock_engine.progress_engine.get_level_from_state.return_value = ProgressLevel.MEDIUM
        mock_engine.progress_engine.get_progress_description.return_value = "Making progress"

        response = test_client.get("/admin/ritual/state/test-user")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "state" in data
        assert "level" in data
        assert "description" in data
        assert data["state"]["user_id"] == "test-user"
        assert data["state"]["progress"] == 50

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_get_user_state_not_found(self, mock_engine_class, test_client):
        """Should return 404 when user state doesn't exist."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_user_state.return_value = None

        response = test_client.get("/admin/ritual/state/nonexistent-user")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_reset_user_state(self, mock_engine_class, test_client):
        """Should reset user state successfully."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        reset_state = RitualState(
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

        mock_engine.reset_user_state.return_value = reset_state

        response = test_client.post("/admin/ritual/state/test-user/reset")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "state" in data
        assert data["state"]["progress"] == 0

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_set_user_progress_success(self, mock_engine_class, test_client):
        """Should set user progress to valid value."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        updated_state = RitualState(
            user_id="test-user",
            progress=75,
            viewed_threads=[],
            viewed_posts=[],
            time_on_site=0,
            first_visit=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            triggers_hit=set(),
            known_patterns={},
        )

        mock_engine.set_user_progress.return_value = updated_state
        # progress_engine is sync, use MagicMock
        mock_engine.progress_engine = MagicMock()
        mock_engine.progress_engine.get_level_from_state.return_value = ProgressLevel.HIGH

        response = test_client.post(
            "/admin/ritual/state/test-user/progress",
            json={"progress": 75}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "state" in data
        assert "level" in data
        assert data["state"]["progress"] == 75

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_set_user_progress_invalid_range(self, mock_engine_class, test_client):
        """Should reject progress outside 0-100 range."""
        # Test value too high
        response = test_client.post(
            "/admin/ritual/state/test-user/progress",
            json={"progress": 150}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test value too low
        response = test_client.post(
            "/admin/ritual/state/test-user/progress",
            json={"progress": -10}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_set_user_progress_not_found(self, mock_engine_class, test_client):
        """Should return 404 when user doesn't exist."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.set_user_progress.return_value = None

        response = test_client.post(
            "/admin/ritual/state/nonexistent/progress",
            json={"progress": 50}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_get_connections(self, mock_engine_class, test_client):
        """Should return active WebSocket connections."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        mock_engine.get_connected_users.return_value = ["user1", "user2", "user3"]
        mock_engine.get_connection_count.return_value = 3

        response = test_client.get("/admin/ritual/connections")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_connections" in data
        assert "connected_users" in data
        assert data["total_connections"] == 3
        assert len(data["connected_users"]) == 3

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_delete_user_state_success(self, mock_engine_class, test_client):
        """Should delete user state successfully."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        mock_state_manager = AsyncMock()
        mock_state_manager.delete.return_value = True
        mock_engine.state_manager = mock_state_manager

        response = test_client.delete("/admin/ritual/state/test-user")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_delete_user_state_not_found(self, mock_engine_class, test_client):
        """Should return 404 when deleting non-existent state."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        mock_state_manager = AsyncMock()
        mock_state_manager.delete.return_value = False
        mock_engine.state_manager = mock_state_manager

        response = test_client.delete("/admin/ritual/state/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRitualAdminAnomalyEndpoints:
    """Tests for anomaly-related endpoints."""

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_trigger_anomaly_success(self, mock_engine_class, test_client):
        """Should queue anomaly for user successfully."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        # Create mock anomaly event
        from app.schemas.anomaly import AnomalyEvent, AnomalyTarget

        mock_event = AnomalyEvent(
            type=AnomalyType.GLITCH,
            severity=AnomalySeverity.MILD,
            target=AnomalyTarget.PAGE,
            duration_ms=3000,
        )

        mock_engine.queue_anomaly_for_type.return_value = mock_event

        response = test_client.post(
            "/admin/ritual/anomaly/test-user",
            json={
                "anomaly_type": "glitch",
                "severity": "mild",
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "event" in data

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_trigger_anomaly_user_not_found(self, mock_engine_class, test_client):
        """Should return 404 when user doesn't exist."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.queue_anomaly_for_type.return_value = None

        response = test_client.post(
            "/admin/ritual/anomaly/nonexistent",
            json={
                "anomaly_type": "glitch",
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_broadcast_anomaly(self, mock_engine_class, test_client):
        """Should broadcast anomaly to all connected users."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        from app.schemas.anomaly import AnomalyEvent, AnomalyTarget

        mock_engine.get_connected_users.return_value = ["user1", "user2"]

        # Mock event creation
        mock_event = AnomalyEvent(
            type=AnomalyType.PRESENCE,
            severity=AnomalySeverity.MODERATE,
            target=AnomalyTarget.PAGE,
        )
        mock_engine.queue_anomaly_for_type.return_value = mock_event

        response = test_client.post(
            "/admin/ritual/broadcast",
            json={
                "anomaly_type": "presence",
                "severity": "moderate",
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "anomaly_type" in data
        assert data["anomaly_type"] == "presence"

    @patch("app.routers.ritual_admin.RitualEngine")
    def test_get_ritual_stats(self, mock_engine_class, test_client):
        """Should return ritual system statistics."""
        # Setup mock
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine

        mock_engine.get_connection_count.return_value = 5

        mock_state_manager = AsyncMock()
        mock_state_manager.get_all_user_ids.return_value = [
            "user1", "user2", "user3"
        ]
        mock_engine.state_manager = mock_state_manager

        # Mock states at different levels
        test_states = [
            RitualState(
                user_id="user1",
                progress=10,
                viewed_threads=[],
                viewed_posts=[],
                time_on_site=0,
                first_visit=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                triggers_hit=set(),
                known_patterns={},
            ),
            RitualState(
                user_id="user2",
                progress=50,
                viewed_threads=[],
                viewed_posts=[],
                time_on_site=0,
                first_visit=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                triggers_hit=set(),
                known_patterns={},
            ),
            RitualState(
                user_id="user3",
                progress=90,
                viewed_threads=[],
                viewed_posts=[],
                time_on_site=0,
                first_visit=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                triggers_hit=set(),
                known_patterns={},
            ),
        ]

        mock_engine.get_user_state.side_effect = test_states
        # progress_engine is sync, use MagicMock
        mock_engine.progress_engine = MagicMock()
        mock_engine.progress_engine.get_level_from_state.side_effect = [
            ProgressLevel.LOW,
            ProgressLevel.MEDIUM,
            ProgressLevel.CRITICAL,
        ]

        response = test_client.get("/admin/ritual/stats")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "active_connections" in data
        assert "total_states" in data
        assert "level_distribution" in data
        assert data["active_connections"] == 5
        assert data["total_states"] == 3
