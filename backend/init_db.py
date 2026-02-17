"""Initialize SQLite database and create admin user for local testing."""
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import async_session
from app.core.security import hash_password
from app.models import Base
from app.models.operator import Operator


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created.")

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
