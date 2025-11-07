"""
Celery application for background tasks and scheduling
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "compliancepro360",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.compliance_tasks", "app.tasks.notification_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    "check-due-date-updates-daily": {
        "task": "app.tasks.compliance_tasks.check_due_date_updates",
        "schedule": crontab(hour=4, minute=0),  # 4 AM IST daily
    },
    "calculate-compliance-scores-daily": {
        "task": "app.tasks.compliance_tasks.calculate_all_compliance_scores",
        "schedule": crontab(hour=5, minute=0),  # 5 AM IST daily
    },
    "send-daily-reminders": {
        "task": "app.tasks.notification_tasks.send_daily_reminders",
        "schedule": crontab(hour=9, minute=0),  # 9 AM IST daily
    },
    "predict-risks-weekly": {
        "task": "app.tasks.compliance_tasks.predict_all_risks",
        "schedule": crontab(day_of_week=1, hour=6, minute=0),  # Monday 6 AM
    },
    "sync-company-data-weekly": {
        "task": "app.tasks.compliance_tasks.sync_all_company_data",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
    },
}

if __name__ == "__main__":
    celery_app.start()
