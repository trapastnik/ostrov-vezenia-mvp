"""Аудит-лог действий администраторов (ФЗ-152, SOC 2)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_operator_id", "operator_id"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_action", "action"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("operators.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "order.status_change", "shop.create"
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "order", "shop", "batch"
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON с деталями
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    operator = relationship("Operator", lazy="selectin")
