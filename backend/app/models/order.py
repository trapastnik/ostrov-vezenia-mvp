import uuid

import json

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class JSONType(TypeDecorator):
    """JSON type that works with both PostgreSQL and SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("shop_id", "external_order_id", name="uq_shop_external_order"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_batch_id", "batch_id"),
        Index("ix_orders_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id"), nullable=False)
    external_order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="accepted", nullable=False)

    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_address: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_postal_code: Mapped[str] = mapped_column(String(6), nullable=False)

    items: Mapped[list] = mapped_column(JSONType, nullable=False)
    total_amount_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)
    total_weight_grams: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_cost_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)
    customs_fee_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)

    track_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    internal_track_number: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("batches.id"), nullable=True)
    shipment_group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("shipment_groups.id"), nullable=True)

    # Тарифы: сохраняем при расчёте для отображения экономии в карточке
    public_tariff_kopecks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contract_tariff_kopecks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tariff_savings_kopecks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tariff_savings_percent: Mapped[float | None] = mapped_column(nullable=True)

    shop = relationship("Shop", back_populates="orders")
    batch = relationship("Batch", back_populates="orders")
    shipment_group = relationship("ShipmentGroup", back_populates="orders")
    status_history = relationship("OrderStatusHistory", back_populates="order", order_by="OrderStatusHistory.created_at")
    tracking_events = relationship(
        "TrackingEvent", back_populates="order",
        order_by="TrackingEvent.created_at",
        foreign_keys="TrackingEvent.order_id",
    )
