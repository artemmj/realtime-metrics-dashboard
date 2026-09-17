# backend/src/tasks/generate_metrics.py
"""Генерация метрик: случайное блуждание + редкие всплески.

Каждый тик генерируются ВСЕ метрики — так у каждой метрики появляются
равномерные точки, а графики на дашборде выглядят живыми и плавными.
"""

import random
from datetime import datetime, timezone

from src.celery_config import celery_app
from src.dependencies.db_dependency import get_sync_session_factory
from src.dependencies.redis_dependency import redis_dependency
from src.models.metric import Metric
from src.schemas.metric import MetricUpdate, MetricWSMessage
from src.services.metric_definitions import (
    METRIC_DEFS,
    MetricDefinition,
    compute_status,
    format_metric_text,
)

PUBLISH_CHANNEL = "metrics:realtime"
LAST_VALUES_KEY = "metrics:last"  # Redis-хеш с последними значениями для walk
SPIKE_CHANCE = 0.03  # вероятность «всплеска» в сторону критической зоны


def _next_value(defn: MetricDefinition, previous: float | None) -> float:
    """Случайное блуждание вокруг рабочего коридора с редкими всплесками."""
    low, high = defn.walk_baseline

    if previous is None:
        value = random.uniform(low, high)
    else:
        value = previous + random.gauss(0, defn.walk_step)
        # Мягкий возврат в коридор (mean reversion), если вышли за границы
        if value < low:
            value = low + (low - value) * 0.25
        elif value > high:
            value = high - (value - high) * 0.25

    # Редкий всплеск в сторону «плохого» значения — драматизм на графиках
    if random.random() < SPIKE_CHANCE:
        if defn.higher_is_bad:
            value += (defn.max - value) * random.uniform(0.5, 0.9)
        else:
            value -= (value - defn.min) * random.uniform(0.4, 0.7)

    return round(min(max(value, defn.min), defn.max), defn.precision)


@celery_app.task(name="generate_metrics")
def generate_metrics():
    """Генерирует все метрики, пишет в БД и публикует готовые WS-конверты в Redis PubSub."""
    redis = redis_dependency.get_sync_client()
    generated: list[str] = []

    for name, defn in METRIC_DEFS.items():
        previous_raw = redis.hget(LAST_VALUES_KEY, name)
        previous = float(previous_raw) if previous_raw is not None else None

        value = _next_value(defn, previous)
        delta = round(value - previous, defn.precision) if previous is not None else 0.0

        metric_data = {
            "name": name,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 1. Сохраняем в БД (синхронно, т.к. мы в Celery worker)
        SessionLocal = get_sync_session_factory()
        with SessionLocal() as session:
            db_metric = Metric(name=name, value=value)
            session.add(db_metric)
            session.commit()
            metric_data["id"] = db_metric.id

        # 2. Обогащаем значение и публикуем готовый конверт для WS-клиентов
        status = compute_status(name, value)
        envelope = MetricWSMessage(
            data=MetricUpdate(
                id=metric_data["id"],
                name=name,
                value=value,
                unit=defn.unit,
                status=status,
                delta=delta,
                text=format_metric_text(name, value, delta, status),
                timestamp=metric_data["timestamp"],
            )
        )
        redis.publish(PUBLISH_CHANNEL, envelope.model_dump_json())

        # 3. Запоминаем значение для следующего шага блуждания
        redis.hset(LAST_VALUES_KEY, name, value)

        generated.append(f"{name}={value}")

    return f"Generated: {', '.join(generated)}"
