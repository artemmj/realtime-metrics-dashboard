from celery import Celery

from src.settings import settings

celery_app = Celery(
    main="backend",
    broker=settings.redis_settings.redis_url,
    backend=settings.redis_settings.redis_url,
)

celery_app.autodiscover_tasks(packages=["src.tasks"])

celery_app.conf.beat_schedule = {
    "generate-metric-every-2-seconds": {
        "task": "generate_metrics",
        "schedule": 2.0,
    },
}
