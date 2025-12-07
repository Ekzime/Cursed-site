"""
Mock data generators for Cursed Board tests.
"""
from datetime import datetime, timedelta
from typing import Optional
import random

from app.schemas.ritual import RitualState
from app.schemas.anomaly import AnomalyType, AnomalySeverity, AnomalyEvent
from app.schemas.trigger import TriggerType


def create_ritual_state(
    user_id: str = "test-user",
    progress: int = 0,
    viewed_threads: Optional[list] = None,
    viewed_posts: Optional[list] = None,
    time_on_site: int = 0,
    triggers_hit: Optional[set] = None,
    known_patterns: Optional[dict] = None,
) -> RitualState:
    """Create a RitualState with customizable fields."""
    return RitualState(
        user_id=user_id,
        progress=progress,
        viewed_threads=viewed_threads or [],
        viewed_posts=viewed_posts or [],
        time_on_site=time_on_site,
        first_visit=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        triggers_hit=triggers_hit or set(),
        known_patterns=known_patterns or {},
    )


def create_state_at_level(level: str) -> RitualState:
    """Create RitualState at specific progress level."""
    level_configs = {
        "low": {"progress": 10, "posts": 5, "time": 300},
        "medium": {"progress": 35, "posts": 25, "time": 1800},
        "high": {"progress": 65, "posts": 100, "time": 3600},
        "critical": {"progress": 90, "posts": 200, "time": 7200},
    }
    config = level_configs.get(level, level_configs["low"])

    return create_ritual_state(
        user_id=f"test-user-{level}",
        progress=config["progress"],
        viewed_posts=list(range(1, config["posts"] + 1)),
        time_on_site=config["time"],
    )


def create_anomaly_event(
    anomaly_type: AnomalyType = AnomalyType.GLITCH,
    severity: AnomalySeverity = AnomalySeverity.MILD,
    post_id: Optional[int] = None,
    thread_id: Optional[int] = None,
) -> AnomalyEvent:
    """Create an AnomalyEvent for testing."""
    return AnomalyEvent(
        type=anomaly_type,
        severity=severity,
        post_id=post_id,
        thread_id=thread_id,
        data={"test": True},
        duration_ms=3000,
    )


# Sample texts for corruption testing
SAMPLE_TEXTS = [
    "Это обычный текст для тестирования.",
    "Привет, как дела? Всё хорошо.",
    "Темно. Очень темно. Ночь не отступает.",
    "Помощь нужна срочно!",
    "Время идёт, но здесь оно течёт иначе.",
]


def get_sample_text(index: int = 0) -> str:
    """Get sample text for testing."""
    return SAMPLE_TEXTS[index % len(SAMPLE_TEXTS)]


def create_post_data(
    post_id: int = 1,
    content: str = "Test post content",
    thread_id: int = 1,
) -> dict:
    """Create post data dict for mutation testing."""
    return {
        "id": post_id,
        "thread_id": thread_id,
        "content": content,
        "username": "test_user",
        "created_at": datetime.utcnow().isoformat(),
    }


def create_thread_data(
    thread_id: int = 1,
    title: str = "Test Thread",
    views: int = 100,
) -> dict:
    """Create thread data dict for mutation testing."""
    return {
        "id": thread_id,
        "title": title,
        "views": views,
        "posts_count": 10,
        "created_at": datetime.utcnow().isoformat(),
    }
