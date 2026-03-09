import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class CustomsDeclaration(Base, TimestampMixin):
    """ДТЭГ — Декларация на товары для экспресс-грузов (Решение ЕЭК №142)."""

    __tablename__ = "customs_declarations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'ready', 'submitted', 'accepted', 'rejected')",
            name="ck_customs_declarations_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    # Связь с партией (1 партия → 1 декларация, опционально)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("batches.id"), nullable=True)

    # draft → ready → submitted → accepted / rejected
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)

    # Счётчики
    orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_weight_grams: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_value_kopecks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_value_usd_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_value_eur_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Место нахождения товаров (графа шапки ДТЭГ)
    goods_location: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Снапшот отправителя (фиксируется при создании)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    sender_address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sender_inn: Mapped[str] = mapped_column(String(12), nullable=False, default="")

    # Таможенный представитель
    customs_rep_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customs_rep_certificate: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Примечание оператора
    operator_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Даты статусов
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Регистрационный номер ФТС (раздел A ДТЭГ, заполняется таможенным органом)
    fts_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    orders = relationship("Order", back_populates="customs_declaration")
    batch = relationship("Batch", back_populates="customs_declaration", foreign_keys=[batch_id])
