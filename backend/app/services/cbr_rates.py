"""Загрузка курсов валют из API ЦБ РФ (cbr-xml-daily.ru) с кешем в Redis."""
import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.company_settings import CompanySettings
from app.services.customs_declaration import get_company_settings

logger = logging.getLogger(__name__)

CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
CACHE_KEY = "ostrov:cbr_rates"
CACHE_TTL = 3600  # 1 час


async def _get_redis():
    """Ленивое подключение к Redis для кеша."""
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        return client
    except Exception:
        return None


async def fetch_cbr_rates() -> dict[str, int]:
    """Получить курсы USD и EUR от ЦБ РФ (с кешем в Redis).

    Returns:
        {"USD": kopecks, "EUR": kopecks}
    """
    # Попытка прочитать из кеша
    redis = await _get_redis()
    if redis:
        try:
            cached = await redis.get(CACHE_KEY)
            if cached:
                logger.debug("CBR rates from cache")
                return json.loads(cached)
        except Exception:
            pass

    # Запрос к ЦБ
    async with httpx.AsyncClient(timeout=10, verify=True) as client:
        resp = await client.get(CBR_API_URL)
        resp.raise_for_status()

    data = resp.json()
    valutes = data.get("Valute", {})

    usd = valutes.get("USD", {})
    eur = valutes.get("EUR", {})

    usd_value = usd.get("Value", 92.5)  # рублей за 1 USD
    eur_value = eur.get("Value", 105.0)  # рублей за 1 EUR

    rates = {
        "USD": int(round(usd_value * 100)),  # копейки
        "EUR": int(round(eur_value * 100)),  # копейки
    }

    # Записать в кеш
    if redis:
        try:
            await redis.set(CACHE_KEY, json.dumps(rates), ex=CACHE_TTL)
            logger.debug("CBR rates cached for %ds", CACHE_TTL)
        except Exception:
            pass

    return rates


async def update_company_rates(db: AsyncSession) -> CompanySettings:
    """Обновить курсы валют в настройках компании из ЦБ РФ.

    Returns:
        Обновлённые настройки компании.
    """
    rates = await fetch_cbr_rates()

    settings_obj = await get_company_settings(db)
    settings_obj.usd_rate_kopecks = rates["USD"]
    settings_obj.eur_rate_kopecks = rates["EUR"]
    settings_obj.rates_updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(settings_obj)

    logger.info(
        "Курсы обновлены из ЦБ РФ: USD=%d коп., EUR=%d коп.",
        rates["USD"],
        rates["EUR"],
    )
    return settings_obj
