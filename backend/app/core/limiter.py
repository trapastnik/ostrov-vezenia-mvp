import logging

from starlette.requests import Request

from slowapi import Limiter

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_real_ip(request: Request) -> str:
    """Получаем реальный IP из X-Forwarded-For (nginx) или remote_addr."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _create_limiter() -> Limiter:
    """Redis используется как общее хранилище счётчиков для всех uvicorn-воркеров.
    Глобальный лимит: 120 запросов/мин на IP (admin-эндпоинты, API).
    Login имеет более строгий лимит (10/мин), заданный явно на эндпоинте.
    В dev-среде без Redis — fallback на in-memory."""
    try:
        return Limiter(
            key_func=get_real_ip,
            storage_uri=settings.REDIS_URL,
            default_limits=["120/minute"],
        )
    except Exception as e:
        logger.warning("Redis unavailable for rate limiter (%s), using in-memory storage", e)
        return Limiter(
            key_func=get_real_ip,
            storage_uri="memory://",
            default_limits=["120/minute"],
        )


limiter = _create_limiter()
