"""
Time utilities for Ritual Engine.
Provides time-based checks for triggers and anomaly generation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo


class TimeOfDay(str, Enum):
    """Time periods for different anomaly behaviors."""
    DAWN = "dawn"        # 5:00 - 7:59
    MORNING = "morning"  # 8:00 - 11:59
    AFTERNOON = "afternoon"  # 12:00 - 17:59
    EVENING = "evening"  # 18:00 - 21:59
    NIGHT = "night"      # 22:00 - 1:59
    WITCHING = "witching"  # 2:00 - 4:59 (the witching hour - peak anomaly time)


def get_current_hour(timezone: Optional[str] = None) -> int:
    """
    Get current hour (0-23).

    Args:
        timezone: Optional timezone string (e.g., 'Europe/Moscow')
                 If None, uses UTC.

    Returns:
        Current hour as integer (0-23)
    """
    if timezone:
        try:
            tz = ZoneInfo(timezone)
            return datetime.now(tz).hour
        except Exception:
            pass
    return datetime.utcnow().hour


def is_night_hour(timezone: Optional[str] = None) -> bool:
    """
    Check if current time is night (22:00 - 5:59).
    Night hours have increased anomaly activity.

    Args:
        timezone: Optional timezone string

    Returns:
        True if current hour is between 22:00 and 05:59
    """
    hour = get_current_hour(timezone)
    return hour >= 22 or hour < 6


def is_witching_hour(timezone: Optional[str] = None) -> bool:
    """
    Check if current time is the witching hour (2:00 - 4:59).
    Maximum anomaly activity period.

    Args:
        timezone: Optional timezone string

    Returns:
        True if current hour is between 2:00 and 4:59
    """
    hour = get_current_hour(timezone)
    return 2 <= hour < 5


def get_time_of_day(timezone: Optional[str] = None) -> TimeOfDay:
    """
    Get current time period.

    Args:
        timezone: Optional timezone string

    Returns:
        TimeOfDay enum value
    """
    hour = get_current_hour(timezone)

    if 2 <= hour < 5:
        return TimeOfDay.WITCHING
    elif 5 <= hour < 8:
        return TimeOfDay.DAWN
    elif 8 <= hour < 12:
        return TimeOfDay.MORNING
    elif 12 <= hour < 18:
        return TimeOfDay.AFTERNOON
    elif 18 <= hour < 22:
        return TimeOfDay.EVENING
    else:  # 22-23 or 0-1
        return TimeOfDay.NIGHT


def get_anomaly_multiplier(timezone: Optional[str] = None) -> float:
    """
    Get anomaly chance multiplier based on time of day.

    Returns:
        Multiplier for anomaly probability (1.0 = normal)
    """
    time_of_day = get_time_of_day(timezone)

    multipliers = {
        TimeOfDay.DAWN: 0.8,       # Calm before the day
        TimeOfDay.MORNING: 0.5,    # Least active
        TimeOfDay.AFTERNOON: 0.7,  # Low activity
        TimeOfDay.EVENING: 1.0,    # Normal
        TimeOfDay.NIGHT: 1.5,      # Increased activity
        TimeOfDay.WITCHING: 2.5,   # Peak activity
    }

    return multipliers.get(time_of_day, 1.0)


def seconds_until_night(timezone: Optional[str] = None) -> int:
    """
    Calculate seconds until night begins (22:00).
    Useful for scheduling night-specific anomalies.

    Returns:
        Seconds until 22:00, or 0 if already night
    """
    if timezone:
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
        except Exception:
            now = datetime.utcnow()
    else:
        now = datetime.utcnow()

    hour = now.hour

    if hour >= 22 or hour < 6:
        return 0  # Already night

    # Calculate seconds until 22:00
    target = now.replace(hour=22, minute=0, second=0, microsecond=0)
    delta = target - now
    return max(0, int(delta.total_seconds()))


def format_time_ago(seconds: int) -> str:
    """
    Format seconds as human-readable time ago string.
    Used for displaying "last seen" and similar.

    Args:
        seconds: Number of seconds

    Returns:
        Human-readable string like "5 минут назад"
    """
    if seconds < 60:
        return "только что"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} мин. назад"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} ч. назад"
    else:
        days = seconds // 86400
        return f"{days} дн. назад"
