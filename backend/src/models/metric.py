from sqlalchemy import Column, String, Float

from src.models.mixins import IDMixin, TimestampsMixin
from src.models.base import Base


class Metric(IDMixin, TimestampsMixin, Base):
    name = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    tags = Column(String(255), nullable=True)
