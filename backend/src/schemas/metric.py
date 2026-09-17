from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MetricOut(BaseModel):
    id: int
    name: str
    value: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricUpdate(BaseModel):
    """Обогащённое значение метрики для realtime-клиентов."""

    id: int
    name: str
    value: float
    unit: str
    status: str
    delta: float
    text: str
    timestamp: datetime


class MetricDefinitionOut(BaseModel):
    """Определение метрики: юнит, диапазон и пороги (единый источник правды)."""

    name: str
    display_name: str
    unit: str
    min: float
    max: float
    precision: int
    warning: float | None
    critical: float | None
    higher_is_bad: bool


class MetricWSMessage(BaseModel):
    type: Literal["metric_update"] = "metric_update"
    data: MetricUpdate


class MetricHistoryMessage(BaseModel):
    """Backfill при подключении: последние точки каждой метрики."""

    type: Literal["history"] = "history"
    data: list[MetricUpdate]


class MetricHelloMessage(BaseModel):
    """Приветствие при подключении: определения всех метрик."""

    type: Literal["hello"] = "hello"
    definitions: list[MetricDefinitionOut]


class PingMessage(BaseModel):
    type: Literal["ping"] = "ping"
