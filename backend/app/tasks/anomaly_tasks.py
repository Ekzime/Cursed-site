"""
Celery tasks for anomaly generation and trigger checking.
"""

import logging
from typing import Optional

import redis
from celery import shared_task

from app.core.settings import settings
from app.schemas.anomaly import AnomalyType
from app.services.ritual_state import RitualStateManager
from app.services.triggers import TriggerChecker
from app.services.progress_engine import ProgressEngine
from app.services.anomaly_generator import AnomalyGenerator
from app.services.anomaly_queue import AnomalyQueue, ConnectionManager


logger = logging.getLogger(__name__)


def _get_redis_client() -> redis.Redis:
    """Get synchronous Redis client for Celery tasks."""
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


@shared_task(name="app.tasks.anomaly_tasks.check_all_triggers")
def check_all_triggers() -> dict:
    """
    Check triggers for all active users.
    Runs every minute via Celery Beat.

    Returns:
        Summary of trigger activations
    """
    redis_client = _get_redis_client()
    state_manager = RitualStateManager(redis_client)
    trigger_checker = TriggerChecker()
    anomaly_queue = AnomalyQueue(redis_client)
    anomaly_generator = AnomalyGenerator()
    connection_manager = ConnectionManager(redis_client)

    # Get connected users only (no point checking offline users)
    connected_users = connection_manager.get_connected_users()

    total_triggers = 0
    total_anomalies = 0

    for user_id in connected_users:
        try:
            state = state_manager.get(user_id)
            if not state:
                continue

            # Check for new triggers
            results = trigger_checker.check_new_triggers(state)

            if not results:
                continue

            # Get aggregated effects
            effects = trigger_checker.get_applicable_effects(results)

            # Apply progress changes
            if effects["total_progress_delta"] != 0:
                state_manager.update_progress(
                    user_id,
                    effects["total_progress_delta"]
                )

            # Record triggered triggers
            for result in results:
                if result.first_activation:
                    state_manager.add_trigger(user_id, result.trigger_type.value)
                    total_triggers += 1

            # Update patterns
            for key, value in effects["patterns_to_set"].items():
                state_manager.update_known_patterns(user_id, key, value)

            # Generate forced anomalies
            for anomaly_type_str in effects["force_anomalies"]:
                try:
                    anomaly_type = AnomalyType(anomaly_type_str)
                    event = anomaly_generator.generate_specific(
                        anomaly_type,
                        state,
                        triggered_by="trigger",
                    )
                    anomaly_queue.push(user_id, event)
                    total_anomalies += 1
                except ValueError:
                    logger.warning(f"Unknown anomaly type: {anomaly_type_str}")

        except Exception as e:
            logger.error(f"Error checking triggers for {user_id}: {e}")

    logger.info(
        f"Trigger check complete: {total_triggers} triggers, "
        f"{total_anomalies} anomalies for {len(connected_users)} users"
    )

    return {
        "users_checked": len(connected_users),
        "triggers_activated": total_triggers,
        "anomalies_generated": total_anomalies,
    }


@shared_task(name="app.tasks.anomaly_tasks.generate_periodic_anomalies")
def generate_periodic_anomalies() -> dict:
    """
    Generate periodic anomalies for connected users.
    Runs every 5 minutes via Celery Beat.

    Returns:
        Summary of generated anomalies
    """
    redis_client = _get_redis_client()
    state_manager = RitualStateManager(redis_client)
    anomaly_queue = AnomalyQueue(redis_client)
    anomaly_generator = AnomalyGenerator()
    connection_manager = ConnectionManager(redis_client)

    connected_users = connection_manager.get_connected_users()
    total_generated = 0

    for user_id in connected_users:
        try:
            state = state_manager.get(user_id)
            if not state:
                continue

            # Check if should generate
            if anomaly_generator.should_generate(state):
                event = anomaly_generator.generate(state)
                anomaly_queue.push(user_id, event)
                total_generated += 1

        except Exception as e:
            logger.error(f"Error generating anomaly for {user_id}: {e}")

    logger.info(f"Periodic generation: {total_generated} anomalies")

    return {
        "users_checked": len(connected_users),
        "anomalies_generated": total_generated,
    }


@shared_task(name="app.tasks.anomaly_tasks.night_anomaly_burst")
def night_anomaly_burst() -> dict:
    """
    Generate burst of anomalies at midnight.
    Special event for night owls.

    Returns:
        Summary of burst
    """
    redis_client = _get_redis_client()
    state_manager = RitualStateManager(redis_client)
    anomaly_queue = AnomalyQueue(redis_client)
    anomaly_generator = AnomalyGenerator()
    connection_manager = ConnectionManager(redis_client)
    progress_engine = ProgressEngine()

    connected_users = connection_manager.get_connected_users()
    total_generated = 0

    for user_id in connected_users:
        try:
            state = state_manager.get(user_id)
            if not state:
                continue

            level = progress_engine.get_level_from_state(state)
            count = anomaly_generator.get_night_burst_count(level)

            events = anomaly_generator.generate_batch(state, count)
            for event in events:
                event.triggered_by = "night_burst"
                anomaly_queue.push(user_id, event)
                total_generated += 1

        except Exception as e:
            logger.error(f"Error in night burst for {user_id}: {e}")

    logger.info(f"Night burst: {total_generated} anomalies")

    return {
        "users_online": len(connected_users),
        "anomalies_generated": total_generated,
    }


@shared_task(name="app.tasks.anomaly_tasks.witching_hour_event")
def witching_hour_event() -> dict:
    """
    Special event at 3 AM - the witching hour.
    Maximum anomaly intensity for all connected users.

    Returns:
        Summary of event
    """
    redis_client = _get_redis_client()
    state_manager = RitualStateManager(redis_client)
    anomaly_queue = AnomalyQueue(redis_client)
    anomaly_generator = AnomalyGenerator()
    connection_manager = ConnectionManager(redis_client)

    connected_users = connection_manager.get_connected_users()
    total_generated = 0

    for user_id in connected_users:
        try:
            state = state_manager.get(user_id)
            if not state:
                continue

            # Special witching hour burst
            events = anomaly_generator.get_witching_hour_burst(state)
            for event in events:
                anomaly_queue.push(user_id, event)
                total_generated += 1

            # Add progress for being online at witching hour
            state_manager.update_progress(user_id, 10)

            # Add trigger
            state_manager.add_trigger(user_id, "witching_hour")

        except Exception as e:
            logger.error(f"Error in witching hour for {user_id}: {e}")

    logger.info(f"Witching hour event: {total_generated} anomalies")

    return {
        "users_online": len(connected_users),
        "anomalies_generated": total_generated,
    }


@shared_task(name="app.tasks.anomaly_tasks.schedule_anomaly")
def schedule_anomaly(
    user_id: str,
    anomaly_type: str,
    delay_seconds: int = 0,
    custom_data: Optional[dict] = None,
) -> dict:
    """
    Schedule a specific anomaly for a user.
    Used by triggers and admin API.

    Args:
        user_id: Target user ID
        anomaly_type: Anomaly type string
        delay_seconds: Delay before delivery
        custom_data: Optional custom data

    Returns:
        Status of scheduling
    """
    redis_client = _get_redis_client()
    state_manager = RitualStateManager(redis_client)
    anomaly_queue = AnomalyQueue(redis_client)
    anomaly_generator = AnomalyGenerator()

    try:
        state = state_manager.get(user_id)
        if not state:
            return {"success": False, "error": "User not found"}

        a_type = AnomalyType(anomaly_type)
        event = anomaly_generator.generate_specific(
            a_type,
            state,
            custom_data=custom_data,
            triggered_by="scheduled",
        )

        if delay_seconds > 0:
            event.delay_ms = delay_seconds * 1000

        anomaly_queue.push(user_id, event)

        return {
            "success": True,
            "event_id": event.id,
            "anomaly_type": anomaly_type,
        }

    except ValueError:
        return {"success": False, "error": f"Unknown anomaly type: {anomaly_type}"}
    except Exception as e:
        logger.error(f"Error scheduling anomaly: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="app.tasks.anomaly_tasks.broadcast_anomaly")
def broadcast_anomaly(
    anomaly_type: str,
    custom_data: Optional[dict] = None,
) -> dict:
    """
    Broadcast an anomaly to all connected users.
    Used for global events.

    Args:
        anomaly_type: Anomaly type string
        custom_data: Optional custom data

    Returns:
        Summary of broadcast
    """
    redis_client = _get_redis_client()
    state_manager = RitualStateManager(redis_client)
    anomaly_queue = AnomalyQueue(redis_client)
    anomaly_generator = AnomalyGenerator()
    connection_manager = ConnectionManager(redis_client)

    try:
        a_type = AnomalyType(anomaly_type)
    except ValueError:
        return {"success": False, "error": f"Unknown anomaly type: {anomaly_type}"}

    connected_users = connection_manager.get_connected_users()
    sent_count = 0

    for user_id in connected_users:
        try:
            state = state_manager.get(user_id)
            if not state:
                continue

            event = anomaly_generator.generate_specific(
                a_type,
                state,
                custom_data=custom_data,
                triggered_by="broadcast",
            )
            anomaly_queue.push(user_id, event)
            sent_count += 1

        except Exception as e:
            logger.error(f"Error broadcasting to {user_id}: {e}")

    return {
        "success": True,
        "users_reached": sent_count,
        "anomaly_type": anomaly_type,
    }
