"""
Anomaly schemas for the Ritual Engine.
Defines anomaly types and events for real-time delivery.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
import uuid


class AnomalyType(str, Enum):
    """Types of anomalies that can occur."""

    # Content anomalies
    NEW_POST = "new_post"           # Fake post appears
    POST_EDIT = "post_edit"         # Post content changes
    POST_CORRUPT = "post_corrupt"   # Text becomes corrupted
    POST_DELETE = "post_delete"     # Post "disappears"

    # Visual anomalies
    GLITCH = "glitch"               # Visual glitch effect
    FLICKER = "flicker"             # Screen flicker
    STATIC = "static"               # Static noise overlay

    # Presence anomalies
    PRESENCE = "presence"           # Someone is watching
    SHADOW = "shadow"               # Shadow movement
    EYES = "eyes"                   # Eyes appear

    # Audio cues (for frontend)
    WHISPER = "whisper"             # Whispered message
    AMBIENT = "ambient"             # Ambient sound change
    HEARTBEAT = "heartbeat"         # Heartbeat sound

    # UI anomalies
    NOTIFICATION = "notification"   # Fake notification
    CURSOR = "cursor"               # Cursor behaves strangely
    SCROLL = "scroll"               # Page scrolls itself
    TYPING = "typing"               # Text types itself

    # Meta anomalies
    VIEWER_COUNT = "viewer_count"   # "Others are reading this"
    RECOGNITION = "recognition"     # Forum "recognizes" user
    MEMORY = "memory"               # References past actions


class AnomalySeverity(str, Enum):
    """Severity levels for anomalies."""
    SUBTLE = "subtle"       # Barely noticeable
    MILD = "mild"           # Noticeable but dismissable
    MODERATE = "moderate"   # Clearly abnormal
    INTENSE = "intense"     # Disturbing
    EXTREME = "extreme"     # Maximum effect


class AnomalyTarget(str, Enum):
    """What the anomaly targets."""
    PAGE = "page"           # Whole page effect
    POST = "post"           # Specific post
    THREAD = "thread"       # Specific thread
    USER = "user"           # User-specific
    CURSOR = "cursor"       # Cursor effects
    TEXT = "text"           # Text content


class AnomalyEvent(BaseModel):
    """Event sent to client when anomaly occurs."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: AnomalyType
    severity: AnomalySeverity = AnomalySeverity.MILD
    target: AnomalyTarget = AnomalyTarget.PAGE

    # Target IDs (optional, depends on target type)
    post_id: Optional[int] = None
    thread_id: Optional[int] = None

    # Payload data for frontend rendering
    data: Dict[str, Any] = Field(default_factory=dict)

    # Timing
    duration_ms: int = Field(default=3000, ge=100, le=60000)
    delay_ms: int = Field(default=0, ge=0)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    triggered_by: Optional[str] = None  # Trigger that caused this

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    def to_ws_message(self) -> dict:
        """Convert to WebSocket message format."""
        return {
            "type": "anomaly",
            "payload": {
                "id": self.id,
                "anomaly_type": self.type.value,
                "severity": self.severity.value,
                "target": self.target.value,
                "post_id": self.post_id,
                "thread_id": self.thread_id,
                "data": self.data,
                "duration_ms": self.duration_ms,
                "delay_ms": self.delay_ms,
                "timestamp": self.timestamp.isoformat(),
            },
        }


# Anomaly templates for quick creation
ANOMALY_TEMPLATES: Dict[AnomalyType, Dict[str, Any]] = {
    AnomalyType.GLITCH: {
        "severity": AnomalySeverity.MILD,
        "target": AnomalyTarget.PAGE,
        "duration_ms": 500,
        "data": {"effect": "rgb_split"},
    },
    AnomalyType.FLICKER: {
        "severity": AnomalySeverity.SUBTLE,
        "target": AnomalyTarget.PAGE,
        "duration_ms": 200,
        "data": {"flicker_count": 3},
    },
    AnomalyType.WHISPER: {
        "severity": AnomalySeverity.MODERATE,
        "target": AnomalyTarget.USER,
        "duration_ms": 5000,
        "data": {"message": "...ты слышишь нас?..."},
    },
    AnomalyType.PRESENCE: {
        "severity": AnomalySeverity.MODERATE,
        "target": AnomalyTarget.PAGE,
        "duration_ms": 8000,
        "data": {"message": "Кто-то смотрит на тебя"},
    },
    AnomalyType.POST_CORRUPT: {
        "severity": AnomalySeverity.INTENSE,
        "target": AnomalyTarget.POST,
        "duration_ms": 10000,
        "data": {"corruption_level": 0.3},
    },
    AnomalyType.NEW_POST: {
        "severity": AnomalySeverity.MODERATE,
        "target": AnomalyTarget.THREAD,
        "duration_ms": 60000,  # Long-lasting (1 minute)
        "data": {},
    },
    AnomalyType.NOTIFICATION: {
        "severity": AnomalySeverity.MILD,
        "target": AnomalyTarget.USER,
        "duration_ms": 5000,
        "data": {"title": "Новое сообщение", "body": "..."},
    },
    AnomalyType.RECOGNITION: {
        "severity": AnomalySeverity.INTENSE,
        "target": AnomalyTarget.USER,
        "duration_ms": 7000,
        "data": {"message": "Мы помним тебя, {username}"},
    },
    AnomalyType.VIEWER_COUNT: {
        "severity": AnomalySeverity.SUBTLE,
        "target": AnomalyTarget.THREAD,
        "duration_ms": 10000,
        "data": {"count": 7, "message": "Сейчас читают: {count}"},
    },
    AnomalyType.CURSOR: {
        "severity": AnomalySeverity.MILD,
        "target": AnomalyTarget.CURSOR,
        "duration_ms": 3000,
        "data": {"behavior": "drift"},
    },
    AnomalyType.TYPING: {
        "severity": AnomalySeverity.INTENSE,
        "target": AnomalyTarget.TEXT,
        "duration_ms": 5000,
        "data": {"text": "ОНИ ЗДЕСЬ"},
    },
    AnomalyType.HEARTBEAT: {
        "severity": AnomalySeverity.MODERATE,
        "target": AnomalyTarget.USER,
        "duration_ms": 10000,
        "data": {"bpm": 80},
    },
}


def create_anomaly(
    anomaly_type: AnomalyType,
    severity: Optional[AnomalySeverity] = None,
    target_id: Optional[int] = None,
    custom_data: Optional[Dict[str, Any]] = None,
    triggered_by: Optional[str] = None,
) -> AnomalyEvent:
    """
    Create an anomaly event from template.

    Args:
        anomaly_type: Type of anomaly
        severity: Override severity (optional)
        target_id: ID of target post/thread (optional)
        custom_data: Override/extend data (optional)
        triggered_by: Trigger that caused this (optional)

    Returns:
        AnomalyEvent ready for delivery
    """
    template = ANOMALY_TEMPLATES.get(anomaly_type, {})

    # Build data
    data = dict(template.get("data", {}))
    if custom_data:
        data.update(custom_data)

    # Determine target type and IDs
    target = template.get("target", AnomalyTarget.PAGE)
    post_id = None
    thread_id = None

    if target == AnomalyTarget.POST:
        post_id = target_id
    elif target == AnomalyTarget.THREAD:
        thread_id = target_id

    return AnomalyEvent(
        type=anomaly_type,
        severity=severity or template.get("severity", AnomalySeverity.MILD),
        target=target,
        post_id=post_id,
        thread_id=thread_id,
        data=data,
        duration_ms=template.get("duration_ms", 3000),
        triggered_by=triggered_by,
    )
