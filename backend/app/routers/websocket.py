"""
WebSocket router for the Ritual Engine.
Real-time delivery of anomalies to connected clients.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState

from app.services.anomaly_queue import AnomalyQueue, ConnectionManager
from app.services.ritual_state import RitualStateManager


router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)

# Constants
HEARTBEAT_INTERVAL = 30  # seconds
QUEUE_POLL_TIMEOUT = 25  # seconds (less than heartbeat)


@router.websocket("/ws/ritual")
async def ritual_websocket(
    websocket: WebSocket,
    fingerprint: Optional[str] = Query(None, alias="fp"),
):
    """
    WebSocket endpoint for ritual anomalies.

    Connection flow:
    1. Client connects with optional fingerprint query param
    2. Server extracts user_id from fingerprint or cookie
    3. Server starts two async tasks:
       - queue_listener: Pops events from Redis queue, sends to client
       - receive_listener: Handles client messages (heartbeat, activity)
    4. On disconnect, cleanup connection state

    Client messages:
    - {"type": "heartbeat"} - Keep connection alive
    - {"type": "activity", "data": {...}} - Report user activity
    - {"type": "ping"} - Ping request, server responds with pong

    Server messages:
    - {"type": "anomaly", "payload": {...}} - Anomaly event
    - {"type": "pong"} - Response to ping
    - {"type": "welcome", "user_id": "..."} - Initial connection confirmation
    """
    # Get Redis from app state
    redis_client = getattr(websocket.app.state, "redis", None)
    if not redis_client:
        logger.error("Redis not available for WebSocket")
        await websocket.close(code=1011, reason="Service unavailable")
        return

    # Extract user ID
    user_id = await _extract_user_id(websocket, fingerprint)
    if not user_id:
        await websocket.close(code=1008, reason="User identification required")
        return

    # Initialize services
    queue = AnomalyQueue(redis_client)
    connection_manager = ConnectionManager(redis_client)
    state_manager = RitualStateManager(redis_client)

    # Accept connection
    await websocket.accept()
    logger.info(f"WebSocket connected: {user_id}")

    # Register connection
    await connection_manager.connect(user_id)

    # Send welcome message
    await _send_json(websocket, {
        "type": "welcome",
        "user_id": user_id,
    })

    # Start listener tasks
    queue_task = asyncio.create_task(
        _queue_listener(websocket, queue, user_id)
    )
    receive_task = asyncio.create_task(
        _receive_listener(websocket, connection_manager, state_manager, user_id)
    )

    try:
        # Wait for either task to complete (usually due to disconnect)
        done, pending = await asyncio.wait(
            [queue_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")

    finally:
        # Cleanup
        await connection_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected: {user_id}")


async def _extract_user_id(
    websocket: WebSocket,
    fingerprint: Optional[str],
) -> Optional[str]:
    """Extract user ID from fingerprint or cookie."""
    # Priority 1: Fingerprint from query param
    if fingerprint:
        return fingerprint

    # Priority 2: Cookie
    cookies = websocket.cookies
    ritual_cookie = cookies.get("ritual_id")
    if ritual_cookie:
        return ritual_cookie

    return None


async def _send_json(websocket: WebSocket, data: dict) -> bool:
    """Safely send JSON message."""
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(data)
            return True
    except Exception as e:
        logger.debug(f"Send failed: {e}")
    return False


async def _queue_listener(
    websocket: WebSocket,
    queue: AnomalyQueue,
    user_id: str,
):
    """Listen for events in user's queue and send to WebSocket."""
    while True:
        try:
            # Check if still connected
            if websocket.client_state != WebSocketState.CONNECTED:
                break

            # Wait for event from queue
            event = await queue.pop_blocking(user_id, timeout=QUEUE_POLL_TIMEOUT)

            if event:
                # Send to client
                success = await _send_json(websocket, event)
                if not success:
                    break

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Queue listener error: {e}")
            await asyncio.sleep(1)  # Prevent tight loop on error


async def _receive_listener(
    websocket: WebSocket,
    connection_manager: ConnectionManager,
    state_manager: RitualStateManager,
    user_id: str,
):
    """Listen for client messages."""
    while True:
        try:
            # Receive message
            data = await websocket.receive_json()

            msg_type = data.get("type")

            if msg_type == "ping":
                await _send_json(websocket, {"type": "pong"})

            elif msg_type == "heartbeat":
                await connection_manager.heartbeat(user_id)

            elif msg_type == "activity":
                # Client reports activity (time spent, actions)
                activity_data = data.get("data", {})
                await _handle_activity(state_manager, user_id, activity_data)

            elif msg_type == "close":
                break

        except WebSocketDisconnect:
            break
        except asyncio.CancelledError:
            break
        except json.JSONDecodeError:
            logger.debug(f"Invalid JSON from {user_id}")
        except Exception as e:
            logger.error(f"Receive listener error: {e}")
            break


async def _handle_activity(
    state_manager: RitualStateManager,
    user_id: str,
    activity_data: dict,
):
    """Handle activity report from client."""
    # Update time on site
    time_spent = activity_data.get("time_spent", 0)
    if time_spent > 0:
        await state_manager.add_time_on_site(user_id, time_spent)

    # Track viewed content
    viewed_thread = activity_data.get("viewed_thread")
    if viewed_thread:
        await state_manager.add_viewed_thread(user_id, viewed_thread)

    viewed_post = activity_data.get("viewed_post")
    if viewed_post:
        await state_manager.add_viewed_post(user_id, viewed_post)
