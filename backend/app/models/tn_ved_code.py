from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TnVedCode(Base):
    """Справочник кодов ТН ВЭД ЕАЭС для ДТЭГ."""

    __tablename__ = "tn_ved_codes"
    __table_args__ = (
        Index("ix_tn_ved_codes_parent", "parent_code"),
        Index("ix_tn_ved_codes_level", "level"),
    )

    code: Mapped[str] = mapped_column(String(10), primary_key=True)  # "6403990000"
    name: Mapped[str] = mapped_column(Text, nullable=False)  # "Обувь на подошве из ..."
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 2=группа, 4=позиция, 6=подпозиция, 10=полный
    parent_code: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "640399" -> "6403"
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Единица измерения
    note: Mapped[str | None] = mapped_column(Text, nullable=True)  # Примечание
