# backend/src/tasks/generate_metrics.py
import random
import json
from datetime import datetime, timezone

from src.celery_config import celery_app
from src.dependencies.db_dependency import get_sync_session_factory
from src.dependencies.redis_dependency import redis_dependency
from src.models.metric import Metric

METRIC_NAMES = ["cpu_usage", "memory_usage", "active_users", "requests_per_sec"]


@celery_app.task(name="generate_metrics")
def generate_metrics():
    """Генерирует метрику, пишет в БД и публикует в Redis PubSub"""
    name = random.choice(METRIC_NAMES)
    value = None
    match name:
        case "cpu_usage":
            value = random.randint(20, 40)
        case "memory_usage":
            value = random.randint(70, 90)
        case "active_users":
            value = random.randint(97, 100)
        case "requests_per_sec":
            value = random.randint(1, 500)

    metric_data = {
        "name": name,
        "value": value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 1. Сохраняем в БД (синхронно, т.к. мы в Celery worker)
    SessionLocal = get_sync_session_factory()
    with SessionLocal() as session:
        db_metric = Metric(
            name=metric_data["name"],
            value=metric_data["value"],
        )
        session.add(db_metric)
        session.commit()
        metric_data["id"] = db_metric.id

    # 2. Публикуем в Redis PubSub для real-time
    r = redis_dependency.get_sync_client()
    r.publish("metrics:realtime", json.dumps(metric_data))

    return f"Generated {metric_data['name']}: {metric_data['value']}"
