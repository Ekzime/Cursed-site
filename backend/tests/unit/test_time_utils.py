"""
Unit tests for time utilities.
TDD: Testing time-based functions with mocked time.
"""
import pytest
from unittest.mock import patch
from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.time_utils import (
    is_night_hour,
    is_witching_hour,
    get_time_of_day,
    get_anomaly_multiplier,
    get_current_hour,
    seconds_until_night,
    format_time_ago,
    TimeOfDay,
)


class TestIsNightHour:
    """Tests for is_night_hour() function."""

    @patch('app.utils.time_utils.get_current_hour')
    def test_22_is_night(self, mock_hour):
        """22:00 should be night."""
        mock_hour.return_value = 22
        assert is_night_hour() is True

    @patch('app.utils.time_utils.get_current_hour')
    def test_23_is_night(self, mock_hour):
        """23:00 should be night."""
        mock_hour.return_value = 23
        assert is_night_hour() is True

    @patch('app.utils.time_utils.get_current_hour')
    def test_0_is_night(self, mock_hour):
        """00:00 should be night."""
        mock_hour.return_value = 0
        assert is_night_hour() is True

    @patch('app.utils.time_utils.get_current_hour')
    def test_5_is_night(self, mock_hour):
        """05:00 should be night."""
        mock_hour.return_value = 5
        assert is_night_hour() is True

    @patch('app.utils.time_utils.get_current_hour')
    def test_6_is_not_night(self, mock_hour):
        """06:00 should NOT be night."""
        mock_hour.return_value = 6
        assert is_night_hour() is False

    @patch('app.utils.time_utils.get_current_hour')
    def test_12_is_not_night(self, mock_hour):
        """12:00 should NOT be night."""
        mock_hour.return_value = 12
        assert is_night_hour() is False

    @patch('app.utils.time_utils.get_current_hour')
    def test_21_is_not_night(self, mock_hour):
        """21:00 should NOT be night."""
        mock_hour.return_value = 21
        assert is_night_hour() is False


class TestIsWitchingHour:
    """Tests for is_witching_hour() function."""

    @patch('app.utils.time_utils.get_current_hour')
    def test_2_is_witching(self, mock_hour):
        """02:00 should be witching hour."""
        mock_hour.return_value = 2
        assert is_witching_hour() is True

    @patch('app.utils.time_utils.get_current_hour')
    def test_3_is_witching(self, mock_hour):
        """03:00 should be witching hour."""
        mock_hour.return_value = 3
        assert is_witching_hour() is True

    @patch('app.utils.time_utils.get_current_hour')
    def test_4_is_witching(self, mock_hour):
        """04:00 should be witching hour."""
        mock_hour.return_value = 4
        assert is_witching_hour() is True

    @patch('app.utils.time_utils.get_current_hour')
    def test_5_is_not_witching(self, mock_hour):
        """05:00 should NOT be witching hour."""
        mock_hour.return_value = 5
        assert is_witching_hour() is False

    @patch('app.utils.time_utils.get_current_hour')
    def test_1_is_not_witching(self, mock_hour):
        """01:00 should NOT be witching hour."""
        mock_hour.return_value = 1
        assert is_witching_hour() is False


class TestGetTimeOfDay:
    """Tests for get_time_of_day() function."""

    @patch('app.utils.time_utils.get_current_hour')
    def test_3am_is_witching(self, mock_hour):
        """03:00 should return WITCHING."""
        mock_hour.return_value = 3
        assert get_time_of_day() == TimeOfDay.WITCHING

    @patch('app.utils.time_utils.get_current_hour')
    def test_6am_is_dawn(self, mock_hour):
        """06:00 should return DAWN."""
        mock_hour.return_value = 6
        assert get_time_of_day() == TimeOfDay.DAWN

    @patch('app.utils.time_utils.get_current_hour')
    def test_10am_is_morning(self, mock_hour):
        """10:00 should return MORNING."""
        mock_hour.return_value = 10
        assert get_time_of_day() == TimeOfDay.MORNING

    @patch('app.utils.time_utils.get_current_hour')
    def test_14_is_afternoon(self, mock_hour):
        """14:00 should return AFTERNOON."""
        mock_hour.return_value = 14
        assert get_time_of_day() == TimeOfDay.AFTERNOON

    @patch('app.utils.time_utils.get_current_hour')
    def test_20_is_evening(self, mock_hour):
        """20:00 should return EVENING."""
        mock_hour.return_value = 20
        assert get_time_of_day() == TimeOfDay.EVENING

    @patch('app.utils.time_utils.get_current_hour')
    def test_23_is_night(self, mock_hour):
        """23:00 should return NIGHT."""
        mock_hour.return_value = 23
        assert get_time_of_day() == TimeOfDay.NIGHT


class TestGetAnomalyMultiplier:
    """Tests for get_anomaly_multiplier() function."""

    @patch('app.utils.time_utils.get_time_of_day')
    def test_morning_has_lowest_multiplier(self, mock_tod):
        """Morning should have lowest multiplier (0.5)."""
        mock_tod.return_value = TimeOfDay.MORNING
        assert get_anomaly_multiplier() == 0.5

    @patch('app.utils.time_utils.get_time_of_day')
    def test_evening_has_normal_multiplier(self, mock_tod):
        """Evening should have normal multiplier (1.0)."""
        mock_tod.return_value = TimeOfDay.EVENING
        assert get_anomaly_multiplier() == 1.0

    @patch('app.utils.time_utils.get_time_of_day')
    def test_night_has_increased_multiplier(self, mock_tod):
        """Night should have increased multiplier (1.5)."""
        mock_tod.return_value = TimeOfDay.NIGHT
        assert get_anomaly_multiplier() == 1.5

    @patch('app.utils.time_utils.get_time_of_day')
    def test_witching_has_highest_multiplier(self, mock_tod):
        """Witching hour should have highest multiplier (2.5)."""
        mock_tod.return_value = TimeOfDay.WITCHING
        assert get_anomaly_multiplier() == 2.5


class TestGetCurrentHour:
    """Tests for get_current_hour() function."""

    @patch('app.utils.time_utils.datetime')
    def test_default_uses_utc(self, mock_datetime):
        """Test that default behavior uses UTC."""
        # Arrange
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 14, 30, 0)

        # Act
        result = get_current_hour()

        # Assert
        assert result == 14
        mock_datetime.utcnow.assert_called_once()

    @patch('app.utils.time_utils.datetime')
    def test_with_valid_timezone(self, mock_datetime):
        """Test with valid timezone string."""
        # Arrange
        moscow_time = datetime(2025, 1, 15, 17, 30, 0, tzinfo=ZoneInfo("Europe/Moscow"))
        mock_datetime.now.return_value = moscow_time

        # Act
        result = get_current_hour("Europe/Moscow")

        # Assert
        assert result == 17
        mock_datetime.now.assert_called_once()

    @patch('app.utils.time_utils.datetime')
    def test_with_invalid_timezone_falls_back_to_utc(self, mock_datetime):
        """Test that invalid timezone falls back to UTC."""
        # Arrange
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 0, 0)

        # Act
        result = get_current_hour("Invalid/Timezone")

        # Assert
        assert result == 10
        mock_datetime.utcnow.assert_called_once()

    @patch('app.utils.time_utils.datetime')
    def test_without_timezone_parameter(self, mock_datetime):
        """Test without timezone parameter (None)."""
        # Arrange
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 22, 45, 0)

        # Act
        result = get_current_hour(None)

        # Assert
        assert result == 22
        mock_datetime.utcnow.assert_called_once()

    @patch('app.utils.time_utils.datetime')
    def test_boundary_hour_0(self, mock_datetime):
        """Test boundary case: hour 0."""
        # Arrange
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 0, 0, 0)

        # Act
        result = get_current_hour()

        # Assert
        assert result == 0

    @patch('app.utils.time_utils.datetime')
    def test_boundary_hour_23(self, mock_datetime):
        """Test boundary case: hour 23."""
        # Arrange
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 23, 59, 59)

        # Act
        result = get_current_hour()

        # Assert
        assert result == 23


class TestSecondsUntilNight:
    """Tests for seconds_until_night() function."""

    @patch('app.utils.time_utils.datetime')
    def test_during_daytime_returns_positive_seconds(self, mock_datetime):
        """Test during daytime returns positive seconds until 22:00."""
        # Arrange: 15:00:00 (3 PM)
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 15, 0, 0)

        # Act
        result = seconds_until_night()

        # Assert
        # From 15:00 to 22:00 = 7 hours = 25200 seconds
        assert result == 25200

    @patch('app.utils.time_utils.datetime')
    def test_during_night_returns_zero(self, mock_datetime):
        """Test during night returns 0."""
        # Arrange: 23:00:00 (11 PM)
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 23, 0, 0)

        # Act
        result = seconds_until_night()

        # Assert
        assert result == 0

    @patch('app.utils.time_utils.datetime')
    def test_during_early_morning_night_returns_zero(self, mock_datetime):
        """Test during early morning night hours returns 0."""
        # Arrange: 02:00:00 (2 AM)
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 2, 0, 0)

        # Act
        result = seconds_until_night()

        # Assert
        assert result == 0

    @patch('app.utils.time_utils.datetime')
    def test_at_boundary_22_00(self, mock_datetime):
        """Test at exactly 22:00 returns 0."""
        # Arrange: 22:00:00
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 22, 0, 0)

        # Act
        result = seconds_until_night()

        # Assert
        assert result == 0

    @patch('app.utils.time_utils.datetime')
    def test_at_boundary_5_59(self, mock_datetime):
        """Test at 05:59 returns 0 (still night)."""
        # Arrange: 05:59:00
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 5, 59, 0)

        # Act
        result = seconds_until_night()

        # Assert
        assert result == 0

    @patch('app.utils.time_utils.datetime')
    def test_at_boundary_6_00(self, mock_datetime):
        """Test at 06:00 returns seconds until 22:00."""
        # Arrange: 06:00:00
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 6, 0, 0)

        # Act
        result = seconds_until_night()

        # Assert
        # From 06:00 to 22:00 = 16 hours = 57600 seconds
        assert result == 57600

    @patch('app.utils.time_utils.datetime')
    def test_with_valid_timezone(self, mock_datetime):
        """Test with valid timezone parameter."""
        # Arrange
        moscow_time = datetime(2025, 1, 15, 14, 30, 0, tzinfo=ZoneInfo("Europe/Moscow"))
        mock_datetime.now.return_value = moscow_time

        # Act
        result = seconds_until_night("Europe/Moscow")

        # Assert
        # From 14:30 to 22:00 = 7.5 hours = 27000 seconds
        assert result == 27000

    @patch('app.utils.time_utils.datetime')
    def test_with_invalid_timezone_falls_back_to_utc(self, mock_datetime):
        """Test with invalid timezone falls back to UTC."""
        # Arrange
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 12, 0, 0)

        # Act
        result = seconds_until_night("Invalid/Timezone")

        # Assert
        # From 12:00 to 22:00 = 10 hours = 36000 seconds
        assert result == 36000
        mock_datetime.utcnow.assert_called()

    @patch('app.utils.time_utils.datetime')
    def test_minutes_before_night(self, mock_datetime):
        """Test a few minutes before night."""
        # Arrange: 21:55:00
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 21, 55, 0)

        # Act
        result = seconds_until_night()

        # Assert
        # From 21:55 to 22:00 = 5 minutes = 300 seconds
        assert result == 300

    @patch('app.utils.time_utils.datetime')
    def test_with_microseconds(self, mock_datetime):
        """Test calculation with microseconds - result is truncated."""
        # Arrange: 10:30:45.123456
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 45, 123456)

        # Act
        result = seconds_until_night()

        # Assert
        # From 10:30:45.123456 to 22:00:00.000000 = ~41354.876544 seconds
        # int() truncates to 41354
        assert result == 41354


class TestFormatTimeAgo:
    """Tests for format_time_ago() function."""

    def test_just_now_0_seconds(self):
        """Test 0 seconds returns 'только что'."""
        # Arrange
        seconds = 0

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "только что"

    def test_just_now_30_seconds(self):
        """Test 30 seconds returns 'только что'."""
        # Arrange
        seconds = 30

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "только что"

    def test_just_now_59_seconds(self):
        """Test 59 seconds returns 'только что'."""
        # Arrange
        seconds = 59

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "только что"

    def test_minutes_1_minute(self):
        """Test 60 seconds returns '1 мин. назад'."""
        # Arrange
        seconds = 60

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "1 мин. назад"

    def test_minutes_5_minutes(self):
        """Test 5 minutes returns '5 мин. назад'."""
        # Arrange
        seconds = 300  # 5 * 60

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "5 мин. назад"

    def test_minutes_30_minutes(self):
        """Test 30 minutes returns '30 мин. назад'."""
        # Arrange
        seconds = 1800  # 30 * 60

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "30 мин. назад"

    def test_minutes_59_minutes(self):
        """Test 59 minutes returns '59 мин. назад'."""
        # Arrange
        seconds = 3599  # 59 * 60 + 59

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "59 мин. назад"

    def test_hours_1_hour(self):
        """Test 1 hour returns '1 ч. назад'."""
        # Arrange
        seconds = 3600  # 60 * 60

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "1 ч. назад"

    def test_hours_5_hours(self):
        """Test 5 hours returns '5 ч. назад'."""
        # Arrange
        seconds = 18000  # 5 * 3600

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "5 ч. назад"

    def test_hours_23_hours(self):
        """Test 23 hours returns '23 ч. назад'."""
        # Arrange
        seconds = 86399  # 24 * 3600 - 1

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "23 ч. назад"

    def test_days_1_day(self):
        """Test 1 day returns '1 дн. назад'."""
        # Arrange
        seconds = 86400  # 24 * 3600

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "1 дн. назад"

    def test_days_7_days(self):
        """Test 7 days returns '7 дн. назад'."""
        # Arrange
        seconds = 604800  # 7 * 24 * 3600

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "7 дн. назад"

    def test_days_30_days(self):
        """Test 30 days returns '30 дн. назад'."""
        # Arrange
        seconds = 2592000  # 30 * 24 * 3600

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "30 дн. назад"

    def test_boundary_60_seconds(self):
        """Test boundary between 'только что' and minutes."""
        # Arrange
        seconds = 60

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "1 мин. назад"

    def test_boundary_3600_seconds(self):
        """Test boundary between minutes and hours."""
        # Arrange
        seconds = 3600

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "1 ч. назад"

    def test_boundary_86400_seconds(self):
        """Test boundary between hours and days."""
        # Arrange
        seconds = 86400

        # Act
        result = format_time_ago(seconds)

        # Assert
        assert result == "1 дн. назад"
