import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_uuid


class CompanySettings(Base, TimestampMixin):
    """Настройки компании-отправителя (синглтон, scope='global')."""

    __tablename__ = "company_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    scope: Mapped[str] = mapped_column(String(30), unique=True, default="global", nullable=False)

    # Данные отправителя (графа «Отправитель» и колонка 4 ДТЭГ)
    company_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    company_address: Mapped[str] = mapped_column(Text, default="", nullable=False)
    company_inn: Mapped[str] = mapped_column(String(12), default="", nullable=False)
    company_kpp: Mapped[str] = mapped_column(String(9), default="", nullable=False)
    company_postal_code: Mapped[str] = mapped_column(String(6), default="238311", nullable=False)
    company_phone: Mapped[str] = mapped_column(String(20), default="", nullable=False)

    # Таможенный представитель
    customs_rep_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    customs_rep_certificate: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    customs_rep_inn: Mapped[str] = mapped_column(String(12), default="", nullable=False)

    # Место нахождения товаров по умолчанию
    goods_location: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    # Курс USD для пересчёта стоимости (копеек за 1 USD)
    usd_rate_kopecks: Mapped[int] = mapped_column(Integer, default=9250, nullable=False)
