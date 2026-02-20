from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ostrov",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL.rsplit("/", 1)[0] + "/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_retry_delay=60,
    task_max_retries=5,
)

celery_app.autodiscover_tasks(["app.workers"])

celery_app.conf.beat_schedule = {
    "run-grouping-optimizer": {
        "task": "tasks_grouping.run_grouping_optimizer",
        "schedule": 30 * 60,  # каждые 30 минут; переопределяется через GroupingSettings
    },
}
