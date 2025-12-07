"""
Unit tests for Pydantic schemas.
TDD: Testing serialization, validation, and transformations.
"""
import pytest
from datetime import datetime
import json

from app.schemas.ritual import RitualState
from app.schemas.anomaly import AnomalyEvent, AnomalyType, AnomalySeverity, create_anomaly
from app.schemas.trigger import TriggerType, TriggerEffect, TRIGGER_EFFECTS


class TestRitualStateSerialization:
    """Tests for RitualState serialization to/from Redis."""

    def test_to_redis_dict_converts_datetime_to_iso(self):
        """Datetimes should be converted to ISO strings."""
        # Arrange
        state = RitualState(
            user_id="test",
            first_visit=datetime(2024, 1, 15, 10, 30, 0),
            last_activity=datetime(2024, 1, 15, 11, 0, 0),
        )

        # Act
        data = state.to_redis_dict()

        # Assert
        assert data["first_visit"] == "2024-01-15T10:30:00"
        assert data["last_activity"] == "2024-01-15T11:00:00"

    def test_to_redis_dict_converts_set_to_list(self):
        """triggers_hit set should be converted to list."""
        # Arrange
        state = RitualState(
            user_id="test",
            triggers_hit={"first_visit", "deep_reader"},
        )

        # Act
        data = state.to_redis_dict()

        # Assert
        assert isinstance(data["triggers_hit"], list)
        assert set(data["triggers_hit"]) == {"first_visit", "deep_reader"}

    def test_from_redis_dict_parses_datetime(self):
        """ISO strings should be parsed back to datetime."""
        # Arrange
        data = {
            "user_id": "test",
            "progress": 50,
            "viewed_threads": [],
            "viewed_posts": [],
            "time_on_site": 0,
            "first_visit": "2024-01-15T10:30:00",
            "last_activity": "2024-01-15T11:00:00",
            "triggers_hit": [],
            "known_patterns": {},
        }

        # Act
        state = RitualState.from_redis_dict(data)

        # Assert
        assert state.first_visit == datetime(2024, 1, 15, 10, 30, 0)
        assert state.last_activity == datetime(2024, 1, 15, 11, 0, 0)

    def test_from_redis_dict_converts_list_to_set(self):
        """triggers_hit list should be converted to set."""
        # Arrange
        data = {
            "user_id": "test",
            "progress": 0,
            "viewed_threads": [],
            "viewed_posts": [],
            "time_on_site": 0,
            "first_visit": "2024-01-15T10:30:00",
            "last_activity": "2024-01-15T11:00:00",
            "triggers_hit": ["first_visit", "deep_reader"],
            "known_patterns": {},
        }

        # Act
        state = RitualState.from_redis_dict(data)

        # Assert
        assert isinstance(state.triggers_hit, set)
        assert state.triggers_hit == {"first_visit", "deep_reader"}

    def test_round_trip_preserves_data(self):
        """to_redis_dict -> from_redis_dict should preserve all data."""
        # Arrange
        original = RitualState(
            user_id="test-user",
            progress=75,
            viewed_threads=[1, 2, 3],
            viewed_posts=[10, 20, 30],
            time_on_site=3600,
            triggers_hit={"first_visit", "halfway"},
            known_patterns={"key": "value"},
        )

        # Act
        data = original.to_redis_dict()
        restored = RitualState.from_redis_dict(data)

        # Assert
        assert restored.user_id == original.user_id
        assert restored.progress == original.progress
        assert restored.viewed_threads == original.viewed_threads
        assert restored.viewed_posts == original.viewed_posts
        assert restored.time_on_site == original.time_on_site
        assert restored.triggers_hit == original.triggers_hit
        assert restored.known_patterns == original.known_patterns


class TestAnomalyEventWebSocket:
    """Tests for AnomalyEvent WebSocket message format."""

    def test_to_ws_message_has_correct_structure(self):
        """WebSocket message should have type and payload."""
        # Arrange
        event = AnomalyEvent(
            type=AnomalyType.GLITCH,
            severity=AnomalySeverity.MILD,
        )

        # Act
        msg = event.to_ws_message()

        # Assert
        assert msg["type"] == "anomaly"
        assert "payload" in msg

    def test_to_ws_message_payload_fields(self):
        """Payload should contain all required fields."""
        # Arrange
        event = AnomalyEvent(
            type=AnomalyType.WHISPER,
            severity=AnomalySeverity.MODERATE,
            post_id=123,
            data={"message": "hello"},
            duration_ms=5000,
        )

        # Act
        msg = event.to_ws_message()
        payload = msg["payload"]

        # Assert
        assert payload["anomaly_type"] == "whisper"
        assert payload["severity"] == "moderate"
        assert payload["post_id"] == 123
        assert payload["data"] == {"message": "hello"}
        assert payload["duration_ms"] == 5000
        assert "timestamp" in payload
        assert "id" in payload

    def test_to_ws_message_is_json_serializable(self):
        """Message should be JSON serializable."""
        # Arrange
        event = AnomalyEvent(
            type=AnomalyType.GLITCH,
            severity=AnomalySeverity.MILD,
            data={"nested": {"value": 1}},
        )

        # Act
        msg = event.to_ws_message()

        # Assert - should not raise
        json_str = json.dumps(msg)
        assert len(json_str) > 0


class TestCreateAnomaly:
    """Tests for create_anomaly helper function."""

    def test_creates_from_template(self):
        """Should create anomaly from template."""
        # Act
        event = create_anomaly(AnomalyType.GLITCH)

        # Assert
        assert event.type == AnomalyType.GLITCH
        assert event.severity is not None
        assert event.duration_ms > 0

    def test_override_severity(self):
        """Should allow overriding severity."""
        # Act
        event = create_anomaly(
            AnomalyType.GLITCH,
            severity=AnomalySeverity.EXTREME,
        )

        # Assert
        assert event.severity == AnomalySeverity.EXTREME

    def test_custom_data_merged(self):
        """Custom data should be merged with template data."""
        # Act
        event = create_anomaly(
            AnomalyType.GLITCH,
            custom_data={"custom": "value"},
        )

        # Assert
        assert event.data.get("custom") == "value"


class TestTriggerEffects:
    """Tests for TRIGGER_EFFECTS configuration."""

    def test_all_trigger_types_have_effects(self):
        """Every TriggerType should have an effect defined."""
        # Arrange
        defined_triggers = set(TRIGGER_EFFECTS.keys())
        all_triggers = set(TriggerType)

        # Assert - at least major triggers should be defined
        major_triggers = {
            TriggerType.FIRST_VISIT,
            TriggerType.DEEP_READER,
            TriggerType.HALFWAY,
            TriggerType.LATE_NIGHT,
        }
        assert major_triggers.issubset(defined_triggers)

    def test_effects_have_valid_values(self):
        """All effects should have valid values."""
        for trigger_type, effect in TRIGGER_EFFECTS.items():
            # Assert
            assert isinstance(effect, TriggerEffect)
            assert effect.anomaly_chance_multiplier >= 0
            # progress_delta can be negative (punishment)
