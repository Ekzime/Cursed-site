"""
Admin API for Ritual Engine testing and debugging.
These endpoints should be protected in production.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.redis import get_redis
from app.schemas.ritual import RitualState
from app.schemas.anomaly import AnomalyType, AnomalySeverity
from app.services.ritual_engine import RitualEngine
from app.services.progress_engine import ProgressLevel


router = APIRouter(prefix="/admin/ritual", tags=["ritual-admin"])


class ProgressUpdate(BaseModel):
    progress: int


class AnomalyRequest(BaseModel):
    anomaly_type: AnomalyType
    severity: Optional[AnomalySeverity] = None
    target_id: Optional[int] = None
    custom_data: Optional[dict] = None


class TriggerRequest(BaseModel):
    trigger_name: str


async def get_engine(redis=Depends(get_redis)) -> RitualEngine:
    """Dependency to get RitualEngine instance."""
    return RitualEngine(redis)


@router.get("/state/{user_id}")
async def get_user_state(
    user_id: str,
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """
    Get user's current ritual state.

    Returns full state including:
    - progress
    - viewed threads/posts
    - triggers hit
    - known patterns
    """
    state = await engine.get_user_state(user_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User state not found",
        )

    return {
        "state": state.model_dump(),
        "level": engine.progress_engine.get_level_from_state(state).value,
        "description": engine.progress_engine.get_progress_description(state.progress),
    }


@router.post("/state/{user_id}/reset")
async def reset_user_state(
    user_id: str,
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """Reset user's state to initial values."""
    state = await engine.reset_user_state(user_id)
    return {
        "message": "State reset successfully",
        "state": state.model_dump(),
    }


@router.post("/state/{user_id}/progress")
async def set_user_progress(
    user_id: str,
    data: ProgressUpdate,
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """Set user's progress to a specific value (0-100)."""
    if not 0 <= data.progress <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress must be between 0 and 100",
        )

    state = await engine.set_user_progress(user_id, data.progress)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User state not found",
        )

    return {
        "message": f"Progress set to {data.progress}",
        "state": state.model_dump(),
        "level": engine.progress_engine.get_level_from_state(state).value,
    }


@router.post("/anomaly/{user_id}")
async def trigger_anomaly(
    user_id: str,
    data: AnomalyRequest,
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """
    Trigger a specific anomaly for a user.

    The anomaly will be queued and delivered via WebSocket
    if the user is connected.
    """
    event = await engine.queue_anomaly_for_type(
        user_id,
        data.anomaly_type,
        data.target_id,
        data.custom_data,
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User state not found",
        )

    return {
        "message": "Anomaly queued",
        "event": event.to_ws_message(),
    }


@router.get("/anomaly/types")
async def list_anomaly_types() -> dict:
    """List all available anomaly types."""
    return {
        "types": [t.value for t in AnomalyType],
        "severities": [s.value for s in AnomalySeverity],
    }


@router.get("/connections")
async def get_connections(
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """Get active WebSocket connection information."""
    users = await engine.get_connected_users()
    count = await engine.get_connection_count()

    return {
        "total_connections": count,
        "connected_users": users,
    }


@router.get("/levels")
async def get_progress_levels() -> dict:
    """Get progress level thresholds and descriptions."""
    engine = ProgressLevel
    return {
        "levels": {
            "low": {"range": "0-20", "description": "Редкие аномалии"},
            "medium": {"range": "21-50", "description": "Иногда происходит странное"},
            "high": {"range": "51-80", "description": "Они знают о тебе"},
            "critical": {"range": "81-100", "description": "Ты один из нас"},
        },
    }


@router.post("/broadcast")
async def broadcast_anomaly(
    data: AnomalyRequest,
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """
    Broadcast an anomaly to all connected users.
    Use with caution!
    """
    users = await engine.get_connected_users()
    sent_count = 0

    for user_id in users:
        event = await engine.queue_anomaly_for_type(
            user_id,
            data.anomaly_type,
            data.target_id,
            data.custom_data,
        )
        if event:
            sent_count += 1

    return {
        "message": f"Anomaly broadcast to {sent_count} users",
        "anomaly_type": data.anomaly_type.value,
    }


@router.get("/stats")
async def get_ritual_stats(
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """Get overall ritual system statistics."""
    connected = await engine.get_connection_count()

    # Get all active states (this is expensive, use carefully)
    all_user_ids = await engine.state_manager.get_all_user_ids()

    level_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }

    for user_id in all_user_ids[:100]:  # Limit to first 100
        state = await engine.get_user_state(user_id)
        if state:
            level = engine.progress_engine.get_level_from_state(state)
            level_counts[level.value] += 1

    return {
        "active_connections": connected,
        "total_states": len(all_user_ids),
        "level_distribution": level_counts,
    }


@router.delete("/state/{user_id}")
async def delete_user_state(
    user_id: str,
    engine: RitualEngine = Depends(get_engine),
) -> dict:
    """Completely delete user's ritual state."""
    deleted = await engine.state_manager.delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User state not found",
        )

    return {"message": "State deleted successfully"}
