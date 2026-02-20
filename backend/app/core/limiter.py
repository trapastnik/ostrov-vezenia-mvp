from starlette.requests import Request

from slowapi import Limiter

from app.core.config import settings


def get_real_ip(request: Request) -> str:
    """Получаем реальный IP из X-Forwarded-For (nginx) или remote_addr."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


# Redis используется как общее хранилище счётчиков для всех uvicorn-воркеров
limiter = Limiter(key_func=get_real_ip, storage_uri=settings.REDIS_URL)
