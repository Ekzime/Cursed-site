"""
Unit tests for ProgressEngine.
TDD: Testing level boundaries and progress calculations.
"""
import pytest
from app.services.progress_engine import ProgressEngine, ProgressLevel
from app.schemas.ritual import RitualState


class TestGetLevel:
    """Tests for ProgressEngine.get_level() method."""

    @pytest.fixture
    def engine(self):
        return ProgressEngine()

    # ==========================================================================
    # Boundary Tests: LOW level (0-20)
    # ==========================================================================

    def test_progress_0_returns_low_level(self, engine):
        """Progress at 0 should return LOW level."""
        # Arrange
        progress = 0

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.LOW

    def test_progress_20_returns_low_level(self, engine):
        """Progress at exactly 20 should still be LOW level."""
        # Arrange
        progress = 20

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.LOW

    def test_progress_10_returns_low_level(self, engine):
        """Progress in middle of LOW range returns LOW."""
        # Arrange
        progress = 10

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.LOW

    # ==========================================================================
    # Boundary Tests: MEDIUM level (21-50)
    # ==========================================================================

    def test_progress_21_returns_medium_level(self, engine):
        """Progress at 21 should return MEDIUM level."""
        # Arrange
        progress = 21

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.MEDIUM

    def test_progress_50_returns_medium_level(self, engine):
        """Progress at exactly 50 should still be MEDIUM level."""
        # Arrange
        progress = 50

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.MEDIUM

    def test_progress_35_returns_medium_level(self, engine):
        """Progress in middle of MEDIUM range returns MEDIUM."""
        # Arrange
        progress = 35

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.MEDIUM

    # ==========================================================================
    # Boundary Tests: HIGH level (51-80)
    # ==========================================================================

    def test_progress_51_returns_high_level(self, engine):
        """Progress at 51 should return HIGH level."""
        # Arrange
        progress = 51

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.HIGH

    def test_progress_80_returns_high_level(self, engine):
        """Progress at exactly 80 should still be HIGH level."""
        # Arrange
        progress = 80

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.HIGH

    # ==========================================================================
    # Boundary Tests: CRITICAL level (81-100)
    # ==========================================================================

    def test_progress_81_returns_critical_level(self, engine):
        """Progress at 81 should return CRITICAL level."""
        # Arrange
        progress = 81

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.CRITICAL

    def test_progress_100_returns_critical_level(self, engine):
        """Progress at 100 should return CRITICAL level."""
        # Arrange
        progress = 100

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.CRITICAL

    # ==========================================================================
    # Edge Cases
    # ==========================================================================

    def test_negative_progress_clamped_to_low(self, engine):
        """Negative progress should be treated as LOW."""
        # Arrange
        progress = -10

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.LOW

    def test_progress_over_100_returns_critical(self, engine):
        """Progress over 100 should return CRITICAL."""
        # Arrange
        progress = 150

        # Act
        level = engine.get_level(progress)

        # Assert
        assert level == ProgressLevel.CRITICAL


class TestApplyProgressDelta:
    """Tests for ProgressEngine.apply_progress_delta() method."""

    @pytest.fixture
    def engine(self):
        return ProgressEngine()

    def test_positive_delta_increases_progress(self, engine):
        """Positive delta should increase progress."""
        # Arrange
        current = 50
        delta = 10

        # Act
        result = engine.apply_progress_delta(current, delta)

        # Assert
        assert result == 60

    def test_negative_delta_decreases_progress(self, engine):
        """Negative delta should decrease progress."""
        # Arrange
        current = 50
        delta = -10

        # Act
        result = engine.apply_progress_delta(current, delta)

        # Assert
        assert result == 40

    def test_progress_cannot_go_below_zero(self, engine):
        """Progress should be clamped to 0 minimum."""
        # Arrange
        current = 5
        delta = -20

        # Act
        result = engine.apply_progress_delta(current, delta)

        # Assert
        assert result == 0

    def test_progress_cannot_exceed_100(self, engine):
        """Progress should be clamped to 100 maximum."""
        # Arrange
        current = 95
        delta = 20

        # Act
        result = engine.apply_progress_delta(current, delta)

        # Assert
        assert result == 100

    def test_zero_delta_no_change(self, engine):
        """Zero delta should not change progress."""
        # Arrange
        current = 50
        delta = 0

        # Act
        result = engine.apply_progress_delta(current, delta)

        # Assert
        assert result == 50


class TestAnomalyChance:
    """Tests for ProgressEngine.get_anomaly_chance() method."""

    @pytest.fixture
    def engine(self):
        return ProgressEngine()

    def test_low_level_has_lowest_base_chance(self, engine, new_user_state):
        """LOW level should have lowest anomaly chance."""
        # Arrange
        new_user_state.progress = 10

        # Act
        chance = engine.get_anomaly_chance(new_user_state)

        # Assert
        assert 0 < chance < 0.1  # Should be around 2% base

    def test_critical_level_has_highest_base_chance(self, engine, critical_progress_state):
        """CRITICAL level should have highest anomaly chance."""
        # Act
        chance = engine.get_anomaly_chance(critical_progress_state)

        # Assert
        assert chance > 0.3  # Should be around 40% base

    def test_multiplier_increases_chance(self, engine, new_user_state):
        """Multiplier should increase anomaly chance."""
        # Arrange
        new_user_state.progress = 10

        # Act
        base_chance = engine.get_anomaly_chance(new_user_state, multiplier=1.0)
        boosted_chance = engine.get_anomaly_chance(new_user_state, multiplier=2.0)

        # Assert
        assert boosted_chance > base_chance

    def test_chance_capped_at_95_percent(self, engine, critical_progress_state):
        """Anomaly chance should never exceed 95%."""
        # Act
        chance = engine.get_anomaly_chance(critical_progress_state, multiplier=100.0)

        # Assert
        assert chance <= 0.95


class TestGetProgressDescription:
    """Tests for ProgressEngine.get_progress_description() method."""

    @pytest.fixture
    def engine(self):
        return ProgressEngine()

    def test_low_level_description(self, engine):
        """LOW level should return appropriate description."""
        # Arrange
        progress = 10

        # Act
        description = engine.get_progress_description(progress)

        # Assert
        assert description == "Всё кажется нормальным..."

    def test_medium_level_description(self, engine):
        """MEDIUM level should return appropriate description."""
        # Arrange
        progress = 35

        # Act
        description = engine.get_progress_description(progress)

        # Assert
        assert description == "Что-то здесь не так."

    def test_high_level_description(self, engine):
        """HIGH level should return appropriate description."""
        # Arrange
        progress = 65

        # Act
        description = engine.get_progress_description(progress)

        # Assert
        assert description == "Они знают, что ты здесь."

    def test_critical_level_description(self, engine):
        """CRITICAL level should return appropriate description."""
        # Arrange
        progress = 90

        # Act
        description = engine.get_progress_description(progress)

        # Assert
        assert description == "Ты один из нас теперь."

    def test_boundary_21_returns_medium_description(self, engine):
        """Progress at boundary 21 should return MEDIUM description."""
        # Arrange
        progress = 21

        # Act
        description = engine.get_progress_description(progress)

        # Assert
        assert description == "Что-то здесь не так."

    def test_boundary_81_returns_critical_description(self, engine):
        """Progress at boundary 81 should return CRITICAL description."""
        # Arrange
        progress = 81

        # Act
        description = engine.get_progress_description(progress)

        # Assert
        assert description == "Ты один из нас теперь."


class TestEstimateActionsToNextLevel:
    """Tests for ProgressEngine.estimate_actions_to_next_level() method."""

    @pytest.fixture
    def engine(self):
        return ProgressEngine()

    def test_low_level_estimates_to_medium(self, engine, new_user_state):
        """LOW level state should estimate actions to reach MEDIUM."""
        # Arrange
        new_user_state.progress = 10

        # Act
        estimate = engine.estimate_actions_to_next_level(new_user_state)

        # Assert
        assert estimate is not None
        assert estimate["progress_needed"] == 11  # 21 - 10
        assert estimate["next_level"] == "medium"
        assert estimate["threads_to_view"] == 11  # 11 / 1
        assert estimate["posts_to_view"] == 22    # 11 / 0.5
        assert estimate["minutes_on_site"] == 110  # 11 / 0.1

    def test_medium_level_estimates_to_high(self, engine, medium_progress_state):
        """MEDIUM level state should estimate actions to reach HIGH."""
        # Arrange
        medium_progress_state.progress = 35

        # Act
        estimate = engine.estimate_actions_to_next_level(medium_progress_state)

        # Assert
        assert estimate is not None
        assert estimate["progress_needed"] == 16  # 51 - 35
        assert estimate["next_level"] == "high"
        assert estimate["threads_to_view"] == 16
        assert estimate["posts_to_view"] == 32
        assert estimate["minutes_on_site"] == 160

    def test_high_level_estimates_to_critical(self, engine):
        """HIGH level state should estimate actions to reach CRITICAL."""
        # Arrange
        state = RitualState(user_id="test", progress=65)

        # Act
        estimate = engine.estimate_actions_to_next_level(state)

        # Assert
        assert estimate is not None
        assert estimate["progress_needed"] == 16  # 81 - 65
        assert estimate["next_level"] == "critical"
        assert estimate["threads_to_view"] == 16
        assert estimate["posts_to_view"] == 32
        assert estimate["minutes_on_site"] == 160

    def test_critical_level_returns_none(self, engine, critical_progress_state):
        """CRITICAL level should return None (already at max)."""
        # Arrange
        critical_progress_state.progress = 90

        # Act
        estimate = engine.estimate_actions_to_next_level(critical_progress_state)

        # Assert
        assert estimate is None

    def test_progress_at_boundary_20(self, engine):
        """Progress at 20 (LOW boundary) should estimate to MEDIUM."""
        # Arrange
        state = RitualState(user_id="test", progress=20)

        # Act
        estimate = engine.estimate_actions_to_next_level(state)

        # Assert
        assert estimate is not None
        assert estimate["progress_needed"] == 1  # 21 - 20
        assert estimate["next_level"] == "medium"

    def test_progress_at_boundary_50(self, engine):
        """Progress at 50 (MEDIUM boundary) should estimate to HIGH."""
        # Arrange
        state = RitualState(user_id="test", progress=50)

        # Act
        estimate = engine.estimate_actions_to_next_level(state)

        # Assert
        assert estimate is not None
        assert estimate["progress_needed"] == 1  # 51 - 50
        assert estimate["next_level"] == "high"

    def test_progress_at_boundary_80(self, engine):
        """Progress at 80 (HIGH boundary) should estimate to CRITICAL."""
        # Arrange
        state = RitualState(user_id="test", progress=80)

        # Act
        estimate = engine.estimate_actions_to_next_level(state)

        # Assert
        assert estimate is not None
        assert estimate["progress_needed"] == 1  # 81 - 80
        assert estimate["next_level"] == "critical"

    def test_progress_at_81_returns_none(self, engine):
        """Progress at 81 (CRITICAL start) should return None."""
        # Arrange
        state = RitualState(user_id="test", progress=81)

        # Act
        estimate = engine.estimate_actions_to_next_level(state)

        # Assert
        assert estimate is None

    def test_progress_at_100_returns_none(self, engine):
        """Progress at 100 (max) should return None."""
        # Arrange
        state = RitualState(user_id="test", progress=100)

        # Act
        estimate = engine.estimate_actions_to_next_level(state)

        # Assert
        assert estimate is None


class TestNextLevel:
    """Tests for ProgressEngine._next_level() private method."""

    @pytest.fixture
    def engine(self):
        return ProgressEngine()

    def test_next_level_from_low_is_medium(self, engine):
        """Next level after LOW should be MEDIUM."""
        # Act
        next_level = engine._next_level(ProgressLevel.LOW)

        # Assert
        assert next_level == ProgressLevel.MEDIUM

    def test_next_level_from_medium_is_high(self, engine):
        """Next level after MEDIUM should be HIGH."""
        # Act
        next_level = engine._next_level(ProgressLevel.MEDIUM)

        # Assert
        assert next_level == ProgressLevel.HIGH

    def test_next_level_from_high_is_critical(self, engine):
        """Next level after HIGH should be CRITICAL."""
        # Act
        next_level = engine._next_level(ProgressLevel.HIGH)

        # Assert
        assert next_level == ProgressLevel.CRITICAL

    def test_next_level_from_critical_stays_critical(self, engine):
        """Next level after CRITICAL should stay CRITICAL."""
        # Act
        next_level = engine._next_level(ProgressLevel.CRITICAL)

        # Assert
        assert next_level == ProgressLevel.CRITICAL
