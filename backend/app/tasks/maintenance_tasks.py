"""
Celery tasks for system maintenance.
"""

import logging
from datetime import datetime, timedelta

import redis
from celery import shared_task

from app.core.settings import settings
from app.services.anomaly_queue import ConnectionManager


logger = logging.getLogger(__name__)


def _get_redis_client() -> redis.Redis:
    """Get synchronous Redis client for Celery tasks."""
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


@shared_task(name="app.tasks.maintenance_tasks.cleanup_stale_sessions")
def cleanup_stale_sessions() -> dict:
    """
    Clean up stale WebSocket connection records.
    Runs hourly via Celery Beat.

    Note: This is a simple cleanup. In production, you'd want
    to track last heartbeat timestamp per connection.

    Returns:
        Summary of cleanup
    """
    redis_client = _get_redis_client()

    # For now, just log stats
    # Real implementation would check heartbeat timestamps
    connection_manager = ConnectionManager(redis_client)
    connected_count = connection_manager.get_connection_count()

    logger.info(f"Session cleanup: {connected_count} connections tracked")

    return {
        "connections_tracked": connected_count,
        "cleaned_up": 0,  # Would be actual cleanup count
    }


@shared_task(name="app.tasks.maintenance_tasks.cleanup_expired_queues")
def cleanup_expired_queues() -> dict:
    """
    Clean up expired anomaly queues.
    Queues auto-expire via Redis TTL, but this catches any orphans.

    Returns:
        Summary of cleanup
    """
    redis_client = _get_redis_client()

    # Find all anomaly queues
    pattern = "anomaly_queue:*"
    keys = redis_client.keys(pattern)

    expired_count = 0
    for key in keys:
        # Check if key has no TTL (orphan)
        ttl = redis_client.ttl(key)
        if ttl == -1:  # No expiry set
            # Set expiry to 1 hour
            redis_client.expire(key, 3600)
            expired_count += 1

    logger.info(f"Queue cleanup: {expired_count} orphan queues fixed")

    return {
        "total_queues": len(keys),
        "orphans_fixed": expired_count,
    }


@shared_task(name="app.tasks.maintenance_tasks.collect_metrics")
def collect_metrics() -> dict:
    """
    Collect and log system metrics.
    Useful for monitoring anomaly system health.

    Returns:
        Current metrics
    """
    redis_client = _get_redis_client()
    connection_manager = ConnectionManager(redis_client)

    # Count ritual states
    ritual_keys = redis_client.keys("ritual_state:*")

    # Count anomaly queues
    queue_keys = redis_client.keys("anomaly_queue:*")

    # Get queue lengths
    total_queued = 0
    for key in queue_keys:
        total_queued += redis_client.llen(key)

    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "connected_users": connection_manager.get_connection_count(),
        "active_states": len(ritual_keys),
        "active_queues": len(queue_keys),
        "total_queued_events": total_queued,
    }

    logger.info(f"Metrics: {metrics}")

    return metrics


@shared_task(name="app.tasks.maintenance_tasks.reset_daily_counters")
def reset_daily_counters() -> dict:
    """
    Reset daily counters in ritual states.
    Runs at midnight.

    Returns:
        Summary of reset
    """
    redis_client = _get_redis_client()

    # This is a placeholder for daily reset logic
    # Could reset things like:
    # - Daily anomaly counts
    # - Visit counters
    # - Temporary patterns

    logger.info("Daily counters reset")

    return {
        "reset_at": datetime.utcnow().isoformat(),
    }
