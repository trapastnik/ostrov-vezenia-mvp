import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Shop(Base, TimestampMixin):
    __tablename__ = "shops"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    customs_fee_kopecks: Mapped[int] = mapped_column(Integer, default=15000, nullable=False)
    sender_postal_code: Mapped[str] = mapped_column(String(6), default="238311", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    orders = relationship("Order", back_populates="shop")
