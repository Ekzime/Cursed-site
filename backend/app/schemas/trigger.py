"""
Trigger schemas for the Ritual Engine.
Defines trigger types, conditions, and effects.
"""

from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    """Types of triggers that can activate based on user behavior."""

    # Visit-based triggers
    FIRST_VISIT = "first_visit"           # First time on the site
    RETURNEE = "returnee"                 # Returned after 7+ days
    FREQUENT_VISITOR = "frequent_visitor" # 5+ visits in a week
    LATE_NIGHT = "late_night"             # Visiting during night hours
    WITCHING_HOUR = "witching_hour"       # Visiting during 2-5 AM

    # Reading behavior triggers
    DEEP_READER = "deep_reader"           # Read 20+ posts
    SPEED_READER = "speed_reader"         # Reading too fast
    SLOW_READER = "slow_reader"           # Lingering on posts
    OBSESSIVE = "obsessive"               # Re-reading same content
    EXPLORER = "explorer"                 # Visited many different boards

    # Progression triggers
    HALFWAY = "halfway"                   # Reached 50% progress
    ALMOST_THERE = "almost_there"         # Reached 80% progress
    ENLIGHTENED = "enlightened"           # Reached 100% progress

    # Special triggers
    FOUND_HIDDEN = "found_hidden"         # Found hidden board/thread
    PATTERN_SEEKER = "pattern_seeker"     # Detected pattern-seeking behavior
    TOO_LONG = "too_long"                 # Spent 1+ hour on site
    MARATHON = "marathon"                 # Spent 3+ hours on site

    # Time-based triggers
    NIGHT_OWL = "night_owl"               # Multiple night visits
    DAWN_VISITOR = "dawn_visitor"         # Visiting at dawn

    # Interaction triggers
    POSTED = "posted"                     # Created a post
    THREAD_CREATOR = "thread_creator"     # Created a thread


class TriggerEffect(BaseModel):
    """Effects that occur when a trigger activates."""

    progress_delta: int = Field(default=0, description="Change in progress (can be negative)")
    anomaly_chance_multiplier: float = Field(default=1.0, ge=0.0, description="Multiplier for anomaly probability")
    unlock_board: Optional[str] = Field(default=None, description="Board slug to unlock")
    unlock_thread: Optional[int] = Field(default=None, description="Thread ID to unlock")
    force_anomaly: Optional[str] = Field(default=None, description="Force specific anomaly type")
    message: Optional[str] = Field(default=None, description="Message to show user")
    set_pattern: Optional[dict] = Field(default=None, description="Pattern data to store")
    cooldown_seconds: int = Field(default=0, description="Cooldown before trigger can fire again")


class TriggerResult(BaseModel):
    """Result of checking a trigger."""

    trigger_type: TriggerType
    activated: bool = False
    first_activation: bool = False  # True if this is the first time trigger fired
    effect: Optional[TriggerEffect] = None
    metadata: dict = Field(default_factory=dict)


class TriggerCheckContext(BaseModel):
    """Context provided to trigger condition functions."""

    user_id: str
    progress: int
    viewed_threads: List[int]
    viewed_posts: List[int]
    time_on_site: int
    first_visit_timestamp: float
    last_activity_timestamp: float
    triggers_hit: set
    known_patterns: dict
    current_path: Optional[str] = None
    current_method: Optional[str] = None
    is_night: bool = False
    is_witching: bool = False
    time_of_day: Optional[str] = None


# Trigger effects configuration
TRIGGER_EFFECTS: dict[TriggerType, TriggerEffect] = {
    TriggerType.FIRST_VISIT: TriggerEffect(
        progress_delta=5,
        message="Добро пожаловать... мы ждали тебя.",
    ),
    TriggerType.RETURNEE: TriggerEffect(
        progress_delta=10,
        anomaly_chance_multiplier=1.3,
        message="Ты вернулся. Мы помним тебя.",
    ),
    TriggerType.FREQUENT_VISITOR: TriggerEffect(
        progress_delta=15,
        anomaly_chance_multiplier=1.5,
    ),
    TriggerType.LATE_NIGHT: TriggerEffect(
        progress_delta=5,
        anomaly_chance_multiplier=1.5,
    ),
    TriggerType.WITCHING_HOUR: TriggerEffect(
        progress_delta=10,
        anomaly_chance_multiplier=2.5,
        force_anomaly="whisper",
    ),
    TriggerType.DEEP_READER: TriggerEffect(
        progress_delta=10,
        anomaly_chance_multiplier=1.5,
    ),
    TriggerType.SPEED_READER: TriggerEffect(
        progress_delta=-5,
        message="Не торопись... прочитай внимательнее.",
    ),
    TriggerType.SLOW_READER: TriggerEffect(
        progress_delta=5,
        set_pattern={"reading_style": "careful"},
    ),
    TriggerType.OBSESSIVE: TriggerEffect(
        progress_delta=15,
        anomaly_chance_multiplier=2.0,
        message="Ты ищешь что-то?",
    ),
    TriggerType.EXPLORER: TriggerEffect(
        progress_delta=10,
        unlock_board="hidden",
    ),
    TriggerType.HALFWAY: TriggerEffect(
        progress_delta=0,
        anomaly_chance_multiplier=1.5,
        message="Половина пути пройдена. Назад дороги нет.",
    ),
    TriggerType.ALMOST_THERE: TriggerEffect(
        progress_delta=0,
        anomaly_chance_multiplier=2.0,
        message="Ты почти у цели. Мы чувствуем тебя.",
    ),
    TriggerType.ENLIGHTENED: TriggerEffect(
        progress_delta=0,
        anomaly_chance_multiplier=3.0,
        unlock_board="void",
        message="Ты видишь правду.",
    ),
    TriggerType.FOUND_HIDDEN: TriggerEffect(
        progress_delta=20,
        anomaly_chance_multiplier=2.0,
    ),
    TriggerType.PATTERN_SEEKER: TriggerEffect(
        progress_delta=10,
        set_pattern={"seeking": True},
    ),
    TriggerType.TOO_LONG: TriggerEffect(
        progress_delta=15,
        anomaly_chance_multiplier=1.8,
        message="Тебе пора отдохнуть... или нет?",
    ),
    TriggerType.MARATHON: TriggerEffect(
        progress_delta=25,
        anomaly_chance_multiplier=2.5,
        force_anomaly="presence",
    ),
    TriggerType.NIGHT_OWL: TriggerEffect(
        progress_delta=15,
        anomaly_chance_multiplier=1.8,
        unlock_board="nightmare",
    ),
    TriggerType.DAWN_VISITOR: TriggerEffect(
        progress_delta=5,
        message="Рассвет близко. Они отступают... пока.",
    ),
    TriggerType.POSTED: TriggerEffect(
        progress_delta=10,
    ),
    TriggerType.THREAD_CREATOR: TriggerEffect(
        progress_delta=15,
        anomaly_chance_multiplier=1.3,
    ),
}
