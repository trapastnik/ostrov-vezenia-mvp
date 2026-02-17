import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Batch(Base, TimestampMixin):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="forming", nullable=False)
    orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_weight_grams: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    customs_presented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customs_cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    orders = relationship("Order", back_populates="batch")
