import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


# Возможные события трекинга
TRACKING_EVENTS = {
    # Уровень заказа
    "order_accepted": "Заказ принят",
    "order_validating": "Проверка данных",
    "order_customs_processing": "Таможенное оформление",
    "order_customs_cleared": "Таможня пройдена",
    "order_awaiting_group": "Ожидает формирования группы",
    # Уровень группы
    "group_formed": "Включён в группу отправки",
    "group_dispatched": "Отправлена группа",
    "group_at_hub": "Группа прибыла в хаб",
    # Уровень последней мили
    "last_mile_transferred": "Передано в доставку",
    "last_mile_in_transit": "В пути",
    "delivered": "Доставлено",
    # Исключения
    "problem": "Проблема с отправлением",
    "cancelled": "Отменено",
}


class TrackingEvent(Base, TimestampMixin):
    """Событие трекинга — привязано к заказу и/или группе."""

    __tablename__ = "tracking_events"
    __table_args__ = (
        Index("ix_tracking_events_order_id", "order_id"),
        Index("ix_tracking_events_shipment_group_id", "shipment_group_id"),
        Index("ix_tracking_events_internal_track_number", "internal_track_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)

    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    shipment_group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("shipment_groups.id"), nullable=True)

    # Внутренний трек-номер (OV-YYYYMMDD-XXXXX)
    internal_track_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    order = relationship("Order", back_populates="tracking_events", foreign_keys=[order_id])
    shipment_group = relationship(
        "ShipmentGroup", back_populates="tracking_events", foreign_keys=[shipment_group_id]
    )
