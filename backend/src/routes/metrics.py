import asyncio
import json
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Annotated, List

from src.dependencies.auth_dependency import get_current_user
from src.schemas.user import UserVerifySchema
from src.dependencies.db_dependency import DBDependency
from src.dependencies.redis_dependency import redis_dependency
from src.models.metric import Metric
from src.schemas.metric import MetricOut  # , MetricWSMessage

router = APIRouter(prefix="/metrics", tags=["Metrics"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass  # Клиент отключился, удалим в следующем цикле


manager = ConnectionManager()


@router.websocket("/ws")
async def metrics_websocket(websocket: WebSocket):
    await websocket.accept()

    async with redis_dependency.get_client() as redis:
        pubsub = redis.pubsub()
        await pubsub.subscribe("metrics:realtime")

        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=0.5
                )

                if message is None:
                    # Нет новых данных — отправляем ping для поддержания соединения
                    await websocket.send_text(json.dumps({"type": "ping"}))
                    await asyncio.sleep(0.5)
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
                await pubsub.unsubscribe("metrics:realtime")
                await pubsub.aclose()
            except Exception:
                pass


@router.get("/", response_model=List[MetricOut])
async def get_metrics_history(
    user: Annotated[UserVerifySchema, Depends(get_current_user)],
    name: str | None = Query(None, description="Filter by metric name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(DBDependency()),
):
    query = select(Metric).order_by(desc(Metric.created_at))

    if name:
        query = query.where(Metric.name == name)

    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    metrics = result.scalars().all()
    return [MetricOut.model_validate(m) for m in metrics]
