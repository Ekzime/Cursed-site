"""
Pydantic schemas for Ritual system.
RitualState tracks user's "curse" progression.
"""

from datetime import datetime
from typing import Optional, Set, List, Dict, Any

from pydantic import BaseModel, Field


class RitualState(BaseModel):
    """
    State of user's ritual/curse progression.
    Stored in Redis with TTL.
    """

    user_id: str = Field(..., description="User identifier (fingerprint + cookie)")
    progress: int = Field(default=0, ge=0, le=100, description="Curse depth 0-100")

    # Viewing history
    viewed_threads: List[int] = Field(default_factory=list)
    viewed_posts: List[int] = Field(default_factory=list)
    time_on_site: int = Field(default=0, description="Total seconds on site")

    # Timestamps
    first_visit: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    # Triggered events
    triggers_hit: Set[str] = Field(default_factory=set)

    # Personalization data (what the "forum knows" about user)
    known_patterns: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}

    def to_redis_dict(self) -> dict:
        """Convert to dict suitable for Redis storage (JSON-serializable)."""
        return {
            "user_id": self.user_id,
            "progress": self.progress,
            "viewed_threads": self.viewed_threads,
            "viewed_posts": self.viewed_posts,
            "time_on_site": self.time_on_site,
            "first_visit": self.first_visit.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "triggers_hit": list(self.triggers_hit),
            "known_patterns": self.known_patterns,
        }

    @classmethod
    def from_redis_dict(cls, data: dict) -> "RitualState":
        """Create RitualState from Redis data."""
        # Convert ISO strings back to datetime
        if isinstance(data.get("first_visit"), str):
            data["first_visit"] = datetime.fromisoformat(data["first_visit"])
        if isinstance(data.get("last_activity"), str):
            data["last_activity"] = datetime.fromisoformat(data["last_activity"])

        # Convert list back to set
        if isinstance(data.get("triggers_hit"), list):
            data["triggers_hit"] = set(data["triggers_hit"])

        return cls(**data)


class RitualStateUpdate(BaseModel):
    """Partial update for RitualState."""

    progress: Optional[int] = Field(None, ge=0, le=100)
    viewed_threads: Optional[List[int]] = None
    viewed_posts: Optional[List[int]] = None
    time_on_site: Optional[int] = None
    triggers_hit: Optional[Set[str]] = None
    known_patterns: Optional[Dict[str, Any]] = None


class RitualStateResponse(BaseModel):
    """Response schema for API endpoints."""

    user_id: str
    progress: int
    threshold_level: str = Field(description="low/medium/high/critical")
    viewed_threads_count: int
    viewed_posts_count: int
    time_on_site: int
    triggers_count: int
    first_visit: datetime
    last_activity: datetime

    @classmethod
    def from_state(cls, state: RitualState) -> "RitualStateResponse":
        """Create response from RitualState."""
        # Determine threshold level
        if state.progress <= 20:
            level = "low"
        elif state.progress <= 50:
            level = "medium"
        elif state.progress <= 80:
            level = "high"
        else:
            level = "critical"

        return cls(
            user_id=state.user_id,
            progress=state.progress,
            threshold_level=level,
            viewed_threads_count=len(state.viewed_threads),
            viewed_posts_count=len(state.viewed_posts),
            time_on_site=state.time_on_site,
            triggers_count=len(state.triggers_hit),
            first_visit=state.first_visit,
            last_activity=state.last_activity,
        )
