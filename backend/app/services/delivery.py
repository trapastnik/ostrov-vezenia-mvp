from dataclasses import dataclass

from app.core.config import settings
from app.models.shop import Shop
from app.services.pochta import PochtaClient


@dataclass
class DeliveryCalculation:
    delivery_cost_kopecks: int
    customs_fee_kopecks: int
    total_cost_kopecks: int
    delivery_days_min: int
    delivery_days_max: int
    available: bool
    rejection_reason: str | None


class DeliveryService:
    def __init__(self, pochta: PochtaClient):
        self._pochta = pochta

    async def calculate(
        self, shop: Shop, postal_code: str, weight_grams: int, total_amount_kopecks: int
    ) -> DeliveryCalculation:
        max_value_kopecks = settings.MAX_PACKAGE_VALUE_USD * settings.USD_RATE_KOPECKS * 100

        if total_amount_kopecks > max_value_kopecks:
            return DeliveryCalculation(
                delivery_cost_kopecks=0,
                customs_fee_kopecks=0,
                total_cost_kopecks=0,
                delivery_days_min=0,
                delivery_days_max=0,
                available=False,
                rejection_reason="exceeds_value_limit",
            )

        if weight_grams > settings.MAX_PACKAGE_WEIGHT_GRAMS:
            return DeliveryCalculation(
                delivery_cost_kopecks=0,
                customs_fee_kopecks=0,
                total_cost_kopecks=0,
                delivery_days_min=0,
                delivery_days_max=0,
                available=False,
                rejection_reason="exceeds_weight_limit",
            )

        try:
            tariff = await self._pochta.calculate_tariff_public(
                index_from=shop.sender_postal_code,
                index_to=postal_code,
                weight_grams=weight_grams,
            )
        except Exception:
            return DeliveryCalculation(
                delivery_cost_kopecks=0,
                customs_fee_kopecks=0,
                total_cost_kopecks=0,
                delivery_days_min=0,
                delivery_days_max=0,
                available=False,
                rejection_reason="delivery_unavailable",
            )

        customs_fee = shop.customs_fee_kopecks
        total = tariff.total_kopecks + customs_fee

        return DeliveryCalculation(
            delivery_cost_kopecks=tariff.total_kopecks,
            customs_fee_kopecks=customs_fee,
            total_cost_kopecks=total,
            delivery_days_min=tariff.min_days,
            delivery_days_max=tariff.max_days,
            available=True,
            rejection_reason=None,
        )
