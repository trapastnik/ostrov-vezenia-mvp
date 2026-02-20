import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UUIDType(TypeDecorator):
    """UUID stored as string for SQLite compatibility."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(str(value))
        return value


class Base(DeclarativeBase):
    type_annotation_map = {
        uuid.UUID: UUIDType,
    }


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()
