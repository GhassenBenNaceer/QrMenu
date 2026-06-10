from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "menutn",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Tunis",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks in app/workers/tasks.py
celery_app.autodiscover_tasks(["app.workers"])
