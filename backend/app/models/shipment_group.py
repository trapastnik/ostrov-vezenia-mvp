import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class ShipmentGroup(Base, TimestampMixin):
    """Группа посылок на магистральном участке Калининград → хаб."""

    __tablename__ = "shipment_groups"
    __table_args__ = (
        Index("ix_shipment_groups_status", "status"),
        Index("ix_shipment_groups_hub", "hub"),
        Index("ix_shipment_groups_scheduled_at", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    # Направление
    hub: Mapped[str] = mapped_column(String(50), nullable=False)           # msk, spb, ekb, nsk, ...
    hub_name: Mapped[str] = mapped_column(String(100), nullable=False)     # Москва, Санкт-Петербург, ...
    transport_type: Mapped[str] = mapped_column(String(20), nullable=False)  # air, truck, rail

    # Статус
    status: Mapped[str] = mapped_column(String(30), default="forming", nullable=False)
    # forming → ready → dispatched → at_hub → completed / cancelled

    # Время
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrived_at_hub_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Статистика
    orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_weight_grams: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Экономия (публичный тариф × N - контрактный тариф группы)
    public_cost_kopecks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contract_cost_kopecks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    savings_kopecks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    savings_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Комментарий оператора
    operator_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    orders = relationship("Order", back_populates="shipment_group")
    tracking_events = relationship(
        "TrackingEvent", back_populates="shipment_group",
        order_by="TrackingEvent.created_at",
        foreign_keys="TrackingEvent.shipment_group_id",
    )
