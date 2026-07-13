from pydantic import BaseModel
from datetime import datetime


class MetricOut(BaseModel):
    id: int
    name: str
    value: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricWSMessage(BaseModel):
    type: str = "metric_update"
    data: MetricOut
