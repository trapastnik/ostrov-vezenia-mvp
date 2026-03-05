"""Загрузка курсов валют из API ЦБ РФ (cbr-xml-daily.ru)."""
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_settings import CompanySettings
from app.services.customs_declaration import get_company_settings

logger = logging.getLogger(__name__)

CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


async def fetch_cbr_rates() -> dict[str, int]:
    """Получить курсы USD и EUR от ЦБ РФ.

    Returns:
        {"USD": kopecks, "EUR": kopecks}
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(CBR_API_URL)
        resp.raise_for_status()

    data = resp.json()
    valutes = data.get("Valute", {})

    usd = valutes.get("USD", {})
    eur = valutes.get("EUR", {})

    usd_value = usd.get("Value", 92.5)  # рублей за 1 USD
    eur_value = eur.get("Value", 105.0)  # рублей за 1 EUR

    return {
        "USD": int(round(usd_value * 100)),  # копейки
        "EUR": int(round(eur_value * 100)),  # копейки
    }


async def update_company_rates(db: AsyncSession) -> CompanySettings:
    """Обновить курсы валют в настройках компании из ЦБ РФ.

    Returns:
        Обновлённые настройки компании.
    """
    rates = await fetch_cbr_rates()

    settings = await get_company_settings(db)
    settings.usd_rate_kopecks = rates["USD"]
    settings.eur_rate_kopecks = rates["EUR"]
    settings.rates_updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(settings)

    logger.info(
        "Курсы обновлены из ЦБ РФ: USD=%d коп., EUR=%d коп.",
        rates["USD"],
        rates["EUR"],
    )
    return settings
