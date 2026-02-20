import uuid

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_uuid


class GroupingSettings(Base, TimestampMixin):
    """Настройки оптимизатора группировки — по одной записи на хаб (или global)."""

    __tablename__ = "grouping_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)

    # Область применения: "global" или код хаба ("msk", "spb", ...)
    scope: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, default="global")
    scope_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Глобальные настройки")

    # Активна ли автогруппировка
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Максимальное ожидание заказа в часах до принудительной отправки
    max_wait_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)

    # Минимальное число заказов для формирования группы
    min_group_size: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Минимальная экономия в рублях, при которой выгодно группировать
    min_savings_rub: Mapped[int] = mapped_column(Integer, default=500, nullable=False)

    # Штраф за час просрочки дедлайна (в рублях, для функции оптимизации)
    penalty_per_hour_rub: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    # Интервал запуска воркера в минутах
    worker_interval_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Описание для операторов
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
