"""
Unit tests for AnomalyGenerator.
TDD: Testing anomaly generation, pools, and severity distribution.
"""
import pytest
from unittest.mock import patch
import random

from app.services.anomaly_generator import AnomalyGenerator
from app.services.progress_engine import ProgressLevel
from app.schemas.anomaly import AnomalyType, AnomalySeverity
from tests.fixtures.mock_data import create_ritual_state, create_state_at_level


class TestShouldGenerate:
    """Tests for AnomalyGenerator.should_generate() method."""

    @pytest.fixture
    def generator(self):
        return AnomalyGenerator()

    def test_returns_boolean(self, generator):
        """should_generate() should return a boolean."""
        # Arrange
        state = create_state_at_level("low")

        # Act
        result = generator.should_generate(state)

        # Assert
        assert isinstance(result, bool)

    @patch('random.random')
    def test_generates_when_random_below_chance(self, mock_random, generator):
        """Should generate when random < chance."""
        # Arrange
        mock_random.return_value = 0.001  # Very low
        state = create_state_at_level("low")

        # Act
        result = generator.should_generate(state)

        # Assert
        assert result is True

    @patch('random.random')
    def test_does_not_generate_when_random_above_chance(self, mock_random, generator):
        """Should not generate when random > chance."""
        # Arrange
        mock_random.return_value = 0.99  # Very high
        state = create_state_at_level("low")

        # Act
        result = generator.should_generate(state)

        # Assert
        assert result is False


class TestGenerate:
    """Tests for AnomalyGenerator.generate() method."""

    @pytest.fixture
    def generator(self):
        return AnomalyGenerator()

    def test_returns_anomaly_event(self, generator):
        """generate() should return an AnomalyEvent."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        event = generator.generate(state)

        # Assert
        assert event is not None
        assert event.type is not None
        assert event.severity is not None

    def test_low_level_uses_low_pool(self, generator):
        """LOW level should use anomalies from LOW pool."""
        # Arrange
        state = create_state_at_level("low")
        random.seed(42)  # For reproducibility

        # Act
        events = [generator.generate(state) for _ in range(20)]

        # Assert
        types = {e.type for e in events}
        low_pool_types = {AnomalyType.GLITCH, AnomalyType.FLICKER,
                         AnomalyType.STATIC, AnomalyType.VIEWER_COUNT}
        assert types.issubset(low_pool_types)

    def test_critical_level_has_more_intense_anomalies(self, generator):
        """CRITICAL level should have more severe anomalies."""
        # Arrange
        state = create_state_at_level("critical")
        random.seed(42)

        # Act
        events = [generator.generate(state) for _ in range(50)]

        # Assert
        severities = [e.severity for e in events]
        intense_count = sum(1 for s in severities
                          if s in [AnomalySeverity.INTENSE, AnomalySeverity.EXTREME])
        # At CRITICAL level, should have significant portion of intense anomalies
        assert intense_count > 10


class TestGenerateSpecific:
    """Tests for AnomalyGenerator.generate_specific() method."""

    @pytest.fixture
    def generator(self):
        return AnomalyGenerator()

    def test_generates_requested_type(self, generator):
        """Should generate the specific anomaly type requested."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        event = generator.generate_specific(AnomalyType.WHISPER, state)

        # Assert
        assert event.type == AnomalyType.WHISPER

    def test_whisper_has_message(self, generator):
        """WHISPER anomaly should have a message in data."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        event = generator.generate_specific(AnomalyType.WHISPER, state)

        # Assert
        assert "message" in event.data
        assert len(event.data["message"]) > 0

    def test_post_corrupt_has_corruption_level(self, generator):
        """POST_CORRUPT anomaly should have corruption_level in data."""
        # Arrange
        state = create_state_at_level("high")

        # Act
        event = generator.generate_specific(AnomalyType.POST_CORRUPT, state)

        # Assert
        assert "corruption_level" in event.data
        assert 0 < event.data["corruption_level"] <= 1.0

    def test_custom_data_merged(self, generator):
        """Custom data should be merged with generated data."""
        # Arrange
        state = create_state_at_level("medium")
        custom = {"custom_field": "custom_value"}

        # Act
        event = generator.generate_specific(
            AnomalyType.WHISPER,
            state,
            custom_data=custom
        )

        # Assert
        assert event.data["custom_field"] == "custom_value"


class TestGenerateBatch:
    """Tests for AnomalyGenerator.generate_batch() method."""

    @pytest.fixture
    def generator(self):
        return AnomalyGenerator()

    def test_generates_correct_count(self, generator):
        """Should generate the requested number of anomalies."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        events = generator.generate_batch(state, count=5)

        # Assert
        assert len(events) == 5

    def test_events_have_staggered_delays(self, generator):
        """Events should have increasing delays."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        events = generator.generate_batch(state, count=3)

        # Assert
        delays = [e.delay_ms for e in events]
        # Each delay should be >= previous
        for i in range(1, len(delays)):
            assert delays[i] >= delays[i-1]


class TestWitchingHourBurst:
    """Tests for AnomalyGenerator.get_witching_hour_burst() method."""

    @pytest.fixture
    def generator(self):
        return AnomalyGenerator()

    def test_returns_multiple_events(self, generator):
        """Should return multiple anomaly events."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        events = generator.get_witching_hour_burst(state)

        # Assert
        assert len(events) >= 3

    def test_events_are_intense(self, generator):
        """Witching hour events should be INTENSE severity."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        events = generator.get_witching_hour_burst(state)

        # Assert
        for event in events:
            assert event.severity == AnomalySeverity.INTENSE

    def test_events_have_witching_trigger(self, generator):
        """Events should have triggered_by='witching_hour'."""
        # Arrange
        state = create_state_at_level("medium")

        # Act
        events = generator.get_witching_hour_burst(state)

        # Assert
        for event in events:
            assert event.triggered_by == "witching_hour"
