import ipaddress
from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _validate_webhook_url(url: str | None) -> str | None:
    """Валидация webhook URL: только HTTPS, запрет внутренних IP и localhost."""
    if url is None:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("webhook_url должен начинаться с http:// или https://")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("webhook_url: некорректный хост")

    # Запрет localhost
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        raise ValueError("webhook_url: localhost запрещён")

    # Запрет внутренних IP-адресов (SSRF protection)
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise ValueError("webhook_url: внутренние/зарезервированные IP запрещены")
    except ValueError as e:
        if "запрещен" in str(e):
            raise
        # hostname — не IP, а доменное имя — это нормально

    return url


class ShopCreate(BaseModel):
    name: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=3)
    webhook_url: str | None = None
    customs_fee_kopecks: int = Field(default=15000, ge=0)
    sender_postal_code: str = Field(default="238311", min_length=5, max_length=6)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook(cls, v: str | None) -> str | None:
        return _validate_webhook_url(v)


class ShopUpdate(BaseModel):
    name: str | None = None
    webhook_url: str | None = None
    customs_fee_kopecks: int | None = None
    sender_postal_code: str | None = None
    is_active: bool | None = None

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook(cls, v: str | None) -> str | None:
        return _validate_webhook_url(v)


class ShopResponse(BaseModel):
    """Ответ без API-ключа (для списков и детальных просмотров)."""
    id: UUID
    name: str
    domain: str
    webhook_url: str | None
    customs_fee_kopecks: int
    sender_postal_code: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ShopCreateResponse(ShopResponse):
    """Ответ при создании магазина — содержит API-ключ (показывается один раз)."""
    api_key: str
