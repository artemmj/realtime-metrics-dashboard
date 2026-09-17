import time
import traceback
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List

from src.dependencies.auth_dependency import get_current_user
from src.dependencies.db_dependency import DBDependency
from src.dependencies.redis_dependency import redis_dependency
from src.models.metric import Metric
from src.schemas.metric import (
    MetricDefinitionOut,
    MetricHelloMessage,
    MetricHistoryMessage,
    MetricOut,
    MetricUpdate,
    PingMessage,
)
from src.schemas.user import UserVerifySchema
from src.services.metric_definitions import METRIC_DEFS, compute_status, format_metric_text

router = APIRouter(prefix="/metrics", tags=["Metrics"])

PUBLISH_CHANNEL = "metrics:realtime"
PING_INTERVAL_SECONDS = 15.0  # heartbeat вместо спама ping каждые 0.5с
BACKFILL_POINTS_PER_METRIC = 30  # точек каждой метрики отдаем при подключении
BACKFILL_WINDOW_MINUTES = 60

# Один инстанс на модуль: движок и пул соединений создаются один раз
db_dependency = DBDependency()


def _build_history_updates(rows: list[Metric]) -> list[MetricUpdate]:
    """Обогащаем исторические строки метрик (юнит, статус, текст)."""
    updates: list[MetricUpdate] = []
    for row in rows:
        defn = METRIC_DEFS.get(row.name)
        if defn is None:
            continue
        status = compute_status(row.name, row.value)
        updates.append(
            MetricUpdate(
                id=row.id,
                name=row.name,
                value=row.value,
                unit=defn.unit,
                status=status,
                delta=0.0,
                text=format_metric_text(row.name, row.value, 0.0, status),
                timestamp=row.created_at,
            )
        )
    return updates


async def send_history(websocket: WebSocket) -> None:
    """Backfill: последние точки каждой метрики — графики живые с первой секунды."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=BACKFILL_WINDOW_MINUTES)

    async with db_dependency.session_factory() as session:
        result = await session.execute(
            select(Metric)
            .where(Metric.created_at >= window_start)
            .order_by(desc(Metric.created_at))
            .limit(BACKFILL_POINTS_PER_METRIC * len(METRIC_DEFS))
        )
        rows = result.scalars().all()

    updates = _build_history_updates(list(reversed(rows)))  # от старых к новым
    await websocket.send_text(MetricHistoryMessage(data=updates).model_dump_json())


@router.websocket("/ws")
async def metrics_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        # 1. Приветствие: определения метрик (юниты, диапазоны, пороги)
        hello = MetricHelloMessage(
            definitions=[
                MetricDefinitionOut.model_validate(defn, from_attributes=True)
                for defn in METRIC_DEFS.values()
            ]
        )
        await websocket.send_text(hello.model_dump_json())

        # 2. История последних точек для мгновенного рендера графиков
        await send_history(websocket)
    except WebSocketDisconnect:
        print("[WS] Client disconnected during init")
        return
    except Exception:
        print(f"[WS ERROR] {traceback.format_exc()}")
        return

    async with redis_dependency.get_client() as redis:
        pubsub = redis.pubsub()
        await pubsub.subscribe(PUBLISH_CHANNEL)

        last_ping = time.monotonic()
        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )

                if message is None:
                    # Нет новых данных — периодический heartbeat
                    if time.monotonic() - last_ping >= PING_INTERVAL_SECONDS:
                        await websocket.send_text(PingMessage().model_dump_json())
                        last_ping = time.monotonic()
                    continue

                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    await websocket.send_text(data)

        except WebSocketDisconnect:
            print("[WS] Client disconnected normally")
        except Exception:
            print(f"[WS ERROR] {traceback.format_exc()}")
        finally:
            try:
                await pubsub.unsubscribe(PUBLISH_CHANNEL)
                await pubsub.aclose()
            except Exception:
                pass


@router.get("/", response_model=List[MetricOut])
async def get_metrics_history(
    user: Annotated[UserVerifySchema, Depends(get_current_user)],
    name: str | None = Query(None, description="Filter by metric name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(db_dependency),
):
    query = select(Metric).order_by(desc(Metric.created_at))

    if name:
        query = query.where(Metric.name == name)

    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    metrics = result.scalars().all()
    return [MetricOut.model_validate(m) for m in metrics]
