"""
Celery application configuration for the Ritual Engine.
Handles background tasks and periodic jobs.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.settings import settings


# Create Celery app
celery_app = Celery(
    "cursed_board",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_URL,
    include=[
        "app.tasks.anomaly_tasks",
        "app.tasks.maintenance_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # Result settings
    result_expires=3600,  # 1 hour

    # Task execution limits
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit

    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Check triggers for all active users every minute
    "check-triggers-every-minute": {
        "task": "app.tasks.anomaly_tasks.check_all_triggers",
        "schedule": 60.0,  # Every minute
    },

    # Generate periodic anomalies every 5 minutes
    "generate-anomalies-5min": {
        "task": "app.tasks.anomaly_tasks.generate_periodic_anomalies",
        "schedule": 300.0,  # Every 5 minutes
    },

    # Cleanup stale sessions hourly
    "cleanup-stale-hourly": {
        "task": "app.tasks.maintenance_tasks.cleanup_stale_sessions",
        "schedule": 3600.0,  # Every hour
    },

    # Night anomaly boost (runs at midnight)
    "night-anomaly-boost": {
        "task": "app.tasks.anomaly_tasks.night_anomaly_burst",
        "schedule": crontab(hour=0, minute=0),
    },

    # Witching hour special (runs at 3 AM)
    "witching-hour-special": {
        "task": "app.tasks.anomaly_tasks.witching_hour_event",
        "schedule": crontab(hour=3, minute=0),
    },
}

# Optional: Configure task routes for different queues
celery_app.conf.task_routes = {
    "app.tasks.anomaly_tasks.*": {"queue": "anomalies"},
    "app.tasks.maintenance_tasks.*": {"queue": "maintenance"},
}


def get_celery_app() -> Celery:
    """Get the Celery application instance."""
    return celery_app
