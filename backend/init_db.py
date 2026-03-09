"""Initialize SQLite database and create admin user for local testing."""
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import async_session
from app.core.security import hash_password
from app.models import Base
from app.models.operator import Operator


# Новые колонки, которые нужно добавить в существующие таблицы.
# create_all НЕ добавляет колонки в существующие таблицы в PostgreSQL.
ALTER_STATEMENTS = [
    # orders: паспортные данные получателя (ДТЭГ)
    ("orders", "recipient_passport_series", "ALTER TABLE orders ADD COLUMN recipient_passport_series VARCHAR(4)"),
    ("orders", "recipient_passport_number", "ALTER TABLE orders ADD COLUMN recipient_passport_number VARCHAR(6)"),
    # company_settings: курс EUR + дата обновления
    ("company_settings", "eur_rate_kopecks", "ALTER TABLE company_settings ADD COLUMN eur_rate_kopecks INTEGER NOT NULL DEFAULT 10500"),
    ("company_settings", "rates_updated_at", "ALTER TABLE company_settings ADD COLUMN rates_updated_at TIMESTAMP WITH TIME ZONE"),
    # customs_declarations: стоимость в евроцентах
    ("customs_declarations", "total_value_eur_cents", "ALTER TABLE customs_declarations ADD COLUMN total_value_eur_cents INTEGER NOT NULL DEFAULT 0"),
    # customs_declarations: связь с партией
    ("customs_declarations", "batch_id", "ALTER TABLE customs_declarations ADD COLUMN batch_id UUID REFERENCES batches(id)"),
]


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created.")

    # Добавить новые колонки в существующие таблицы (безопасно — игнорируем ошибку если уже есть)
    async with engine.begin() as conn:
        for table, column, stmt in ALTER_STATEMENTS:
            try:
                await conn.execute(text(stmt))
                print(f"  + {table}.{column} added")
            except Exception:
                print(f"  ~ {table}.{column} already exists")

    async with async_session() as db:
        admin = Operator(
            name="Администратор",
            email="admin@ostrov.ru",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)
        try:
            await db.commit()
            print("Admin user created: admin@ostrov.ru / admin123")
        except Exception:
            print("Admin user already exists.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
