"""
Unit tests for TriggerChecker.
TDD: Testing trigger conditions and effect aggregation.
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from app.services.triggers import TriggerChecker
from app.schemas.trigger import TriggerType, TriggerResult
from app.schemas.ritual import RitualState
from tests.fixtures.mock_data import create_ritual_state


class TestTriggerConditions:
    """Tests for individual trigger conditions."""

    @pytest.fixture
    def checker(self):
        return TriggerChecker()

    # ==========================================================================
    # FIRST_VISIT trigger
    # ==========================================================================

    def test_first_visit_fires_at_zero_progress(self, checker):
        """FIRST_VISIT should fire when progress is 0."""
        # Arrange
        state = create_ritual_state(progress=0)

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.FIRST_VISIT]
        assert len(triggered) == 1
        assert triggered[0].activated is True

    def test_first_visit_does_not_fire_with_progress(self, checker):
        """FIRST_VISIT should NOT fire when progress > 0."""
        # Arrange
        state = create_ritual_state(progress=10)

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.FIRST_VISIT]
        assert len(triggered) == 0

    # ==========================================================================
    # DEEP_READER trigger
    # ==========================================================================

    def test_deep_reader_fires_at_20_posts(self, checker):
        """DEEP_READER should fire when viewed_posts >= 20."""
        # Arrange
        state = create_ritual_state(
            progress=10,
            viewed_posts=list(range(1, 21)),  # 20 posts
        )

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.DEEP_READER]
        assert len(triggered) == 1

    def test_deep_reader_does_not_fire_at_19_posts(self, checker):
        """DEEP_READER should NOT fire when viewed_posts < 20."""
        # Arrange
        state = create_ritual_state(
            progress=10,
            viewed_posts=list(range(1, 20)),  # 19 posts
        )

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.DEEP_READER]
        assert len(triggered) == 0

    # ==========================================================================
    # TOO_LONG trigger
    # ==========================================================================

    def test_too_long_fires_at_1_hour(self, checker):
        """TOO_LONG should fire when time_on_site >= 3600 seconds."""
        # Arrange
        state = create_ritual_state(
            progress=10,
            time_on_site=3600,  # 1 hour
        )

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.TOO_LONG]
        assert len(triggered) == 1

    def test_too_long_does_not_fire_under_1_hour(self, checker):
        """TOO_LONG should NOT fire when time_on_site < 3600."""
        # Arrange
        state = create_ritual_state(
            progress=10,
            time_on_site=3599,
        )

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.TOO_LONG]
        assert len(triggered) == 0

    # ==========================================================================
    # MARATHON trigger
    # ==========================================================================

    def test_marathon_fires_at_3_hours(self, checker):
        """MARATHON should fire when time_on_site >= 10800 seconds."""
        # Arrange
        state = create_ritual_state(
            progress=10,
            time_on_site=10800,  # 3 hours
        )

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.MARATHON]
        assert len(triggered) == 1

    # ==========================================================================
    # HALFWAY trigger
    # ==========================================================================

    def test_halfway_fires_at_50_progress(self, checker):
        """HALFWAY should fire when progress >= 50."""
        # Arrange
        state = create_ritual_state(progress=50)

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.HALFWAY]
        assert len(triggered) == 1

    def test_halfway_does_not_fire_under_50(self, checker):
        """HALFWAY should NOT fire when progress < 50."""
        # Arrange
        state = create_ritual_state(progress=49)

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.HALFWAY]
        assert len(triggered) == 0

    # ==========================================================================
    # Night-based triggers (with mocking)
    # ==========================================================================

    @patch('app.services.triggers.is_night_hour')
    def test_late_night_fires_at_night(self, mock_night, checker):
        """LATE_NIGHT should fire during night hours."""
        # Arrange
        mock_night.return_value = True
        state = create_ritual_state(progress=10)

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.LATE_NIGHT]
        assert len(triggered) == 1

    @patch('app.services.triggers.is_night_hour')
    def test_late_night_does_not_fire_during_day(self, mock_night, checker):
        """LATE_NIGHT should NOT fire during day."""
        # Arrange
        mock_night.return_value = False
        state = create_ritual_state(progress=10)

        # Act
        results = checker.check_all(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.LATE_NIGHT]
        assert len(triggered) == 0


class TestCheckNewTriggers:
    """Tests for check_new_triggers method."""

    @pytest.fixture
    def checker(self):
        return TriggerChecker()

    def test_skips_already_hit_triggers(self, checker):
        """Should skip triggers that have already been hit."""
        # Arrange
        state = create_ritual_state(
            progress=0,
            triggers_hit={"first_visit"},  # Already hit
        )

        # Act
        results = checker.check_new_triggers(state)

        # Assert
        triggered = [r for r in results if r.trigger_type == TriggerType.FIRST_VISIT]
        assert len(triggered) == 0

    def test_returns_new_triggers_only(self, checker):
        """Should only return triggers not in triggers_hit."""
        # Arrange
        state = create_ritual_state(
            progress=50,
            triggers_hit={"first_visit"},  # Already hit
        )

        # Act
        results = checker.check_new_triggers(state)

        # Assert
        trigger_types = {r.trigger_type for r in results}
        assert TriggerType.FIRST_VISIT not in trigger_types
        assert TriggerType.HALFWAY in trigger_types


class TestGetApplicableEffects:
    """Tests for effect aggregation."""

    @pytest.fixture
    def checker(self):
        return TriggerChecker()

    def test_aggregates_progress_deltas(self, checker):
        """Should sum progress deltas from multiple triggers."""
        # Arrange
        results = [
            TriggerResult(
                trigger_type=TriggerType.FIRST_VISIT,
                activated=True,
                first_activation=True,
                effect=checker.trigger_checker._conditions if hasattr(checker, 'trigger_checker') else None,
            ),
        ]
        # Use actual check_all to get real results
        state = create_ritual_state(progress=0, time_on_site=3600)
        results = checker.check_all(state)

        # Act
        effects = checker.get_applicable_effects(results)

        # Assert
        assert "total_progress_delta" in effects
        assert effects["total_progress_delta"] >= 0

    def test_gets_max_multiplier(self, checker):
        """Should return maximum anomaly multiplier."""
        # Arrange
        state = create_ritual_state(progress=0, time_on_site=3600)
        results = checker.check_all(state)

        # Act
        effects = checker.get_applicable_effects(results)

        # Assert
        assert "max_anomaly_multiplier" in effects
        assert effects["max_anomaly_multiplier"] >= 1.0

    def test_collects_messages(self, checker):
        """Should collect messages from triggered effects."""
        # Arrange
        state = create_ritual_state(progress=0)
        results = checker.check_all(state)

        # Act
        effects = checker.get_applicable_effects(results)

        # Assert
        assert "messages" in effects
        assert isinstance(effects["messages"], list)
