from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

# SQLite не поддерживает pool_size/max_overflow — настройки только для PostgreSQL
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {"echo": False}
if not _is_sqlite:
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
