from starlette.requests import Request

from slowapi import Limiter


def get_real_ip(request: Request) -> str:
    """Получаем реальный IP из X-Real-IP (проброшен nginx) или из remote_addr."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_real_ip)
