"""
Оптимизатор группировки отправок.

Математика:
    score(group) = savings(group) - penalty(group)

    savings(group) = public_total_kopecks - contract_total_kopecks
        - public_total_kopecks: сумма публичных тарифов для каждой посылки по отдельности
        - contract_total_kopecks: контрактный тариф на суммарный вес группы

    penalty(group) = sum(max(0, delay_hours_i) * penalty_per_hour_rub * 100)
        - delay_hours_i: часов, на которые заказ i превысил свой дедлайн
        - дедлайн = created_at + max_wait_hours

Решение: отправить группу, если:
    1. score > 0  (экономия перевешивает штрафы)
    2. ИЛИ любой заказ в группе превысил свой дедлайн (принудительная отправка)
    3. ИЛИ накопилось >= min_group_size заказов И savings >= min_savings_rub
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grouping_settings import GroupingSettings
from app.models.order import Order
from app.models.shipment_group import ShipmentGroup
from app.models.tracking_event import TrackingEvent
from app.services.hub_router import get_hub_for_postal_code, HUB_REGISTRY
from app.services.pochta import PochtaClient

logger = logging.getLogger(__name__)


@dataclass
class GroupDecision:
    hub: str
    orders: list[Order]
    savings_kopecks: int
    savings_percent: float
    public_cost_kopecks: int
    contract_cost_kopecks: int
    reason: str  # "score", "deadline_exceeded", "min_size_reached", "forced"


class GroupingOptimizer:
    def __init__(self, session: AsyncSession, pochta_client: PochtaClient):
        self._session = session
        self._pochta = pochta_client

    async def run(self, sender_postal_code: str = "238311") -> list[GroupDecision]:
        """Основной метод — анализирует все pending-заказы и возвращает решения."""
        settings = await self._load_settings()
        if not settings.enabled:
            return []

        orders = await self._load_pending_orders()
        if not orders:
            return []

        # Группируем по хабу
        by_hub: dict[str, list[Order]] = {}
        for order in orders:
            hub = get_hub_for_postal_code(order.recipient_postal_code)
            by_hub.setdefault(hub, []).append(order)

        decisions = []
        for hub, hub_orders in by_hub.items():
            decision = await self._evaluate_hub(
                hub, hub_orders, settings, sender_postal_code
            )
            if decision is not None:
                decisions.append(decision)

        return decisions

    async def apply_decision(self, decision: GroupDecision, operator_id=None) -> ShipmentGroup:
        """Создаёт ShipmentGroup и TrackingEvent для принятого решения."""
        hub_info = HUB_REGISTRY.get(decision.hub, {})
        group_number = self._generate_group_number(decision.hub)

        group = ShipmentGroup(
            number=group_number,
            hub=decision.hub,
            hub_name=hub_info.get("name", decision.hub),
            transport_type=hub_info.get("transport", "truck"),
            status="forming",
            orders_count=len(decision.orders),
            total_weight_grams=sum(o.total_weight_grams for o in decision.orders),
            public_cost_kopecks=decision.public_cost_kopecks,
            contract_cost_kopecks=decision.contract_cost_kopecks,
            savings_kopecks=decision.savings_kopecks,
            savings_percent=decision.savings_percent,
        )
        self._session.add(group)
        await self._session.flush()  # получаем group.id

        now = datetime.now(timezone.utc)
        for order in decision.orders:
            order.shipment_group_id = group.id
            order.internal_track_number = self._generate_track_number(order)
            order.status = "awaiting_pickup"

            event = TrackingEvent(
                order_id=order.id,
                shipment_group_id=group.id,
                internal_track_number=order.internal_track_number,
                event_type="group_formed",
                description=f"Включён в группу {group_number} → {group.hub_name}",
                location="Калининград",
            )
            self._session.add(event)

        await self._session.commit()
        logger.info(
            "Создана группа %s: %d заказов, экономия %d коп. (%s%%)",
            group_number, len(decision.orders), decision.savings_kopecks, decision.savings_percent,
        )
        return group

    # ── private ──────────────────────────────────────────────────────────────

    async def _evaluate_hub(
        self,
        hub: str,
        orders: list[Order],
        settings: GroupingSettings,
        sender_postal_code: str,
    ) -> GroupDecision | None:
        now = datetime.now(timezone.utc)

        # Считаем дедлайны
        deadlines = {
            o.id: o.created_at.replace(tzinfo=timezone.utc)
            if o.created_at.tzinfo is None
            else o.created_at
            for o in orders
        }
        deadline_exceeded = any(
            (now - deadlines[o.id]).total_seconds() / 3600 > settings.max_wait_hours
            for o in orders
        )

        # Получаем тарифы
        try:
            tariffs = await self._get_group_tariffs(orders, sender_postal_code)
        except Exception as e:
            logger.warning("Не удалось получить тарифы для хаба %s: %s", hub, e)
            # При ошибке тарифов — форсируем если есть просрочка
            if deadline_exceeded:
                return GroupDecision(
                    hub=hub, orders=orders,
                    savings_kopecks=0, savings_percent=0.0,
                    public_cost_kopecks=0, contract_cost_kopecks=0,
                    reason="deadline_exceeded",
                )
            return None

        public_total = tariffs["public_total"]
        contract_total = tariffs["contract_total"]
        savings = public_total - contract_total
        savings_pct = round(savings / public_total * 100, 1) if public_total > 0 else 0.0

        # Считаем штрафы за просрочку дедлайнов
        total_penalty_kopecks = 0
        for o in orders:
            hours_over = max(
                0,
                (now - deadlines[o.id]).total_seconds() / 3600 - settings.max_wait_hours,
            )
            total_penalty_kopecks += int(hours_over * settings.penalty_per_hour_rub * 100)

        score = savings - total_penalty_kopecks

        # Принимаем решение
        reason = None
        if deadline_exceeded:
            reason = "deadline_exceeded"
        elif score > 0 and savings >= settings.min_savings_rub * 100 and len(orders) >= settings.min_group_size:
            reason = "score"
        elif len(orders) >= settings.min_group_size and savings >= settings.min_savings_rub * 100:
            reason = "min_size_reached"

        if reason is None:
            return None

        return GroupDecision(
            hub=hub,
            orders=orders,
            savings_kopecks=savings,
            savings_percent=savings_pct,
            public_cost_kopecks=public_total,
            contract_cost_kopecks=contract_total,
            reason=reason,
        )

    async def _get_group_tariffs(self, orders: list[Order], sender_postal_code: str) -> dict:
        """
        public_total = сумма тарифов для каждого заказа по отдельности (публичный)
        contract_total = тариф на суммарный вес (контрактный)
        """
        total_weight = sum(o.total_weight_grams for o in orders)
        # Берём репрезентативный индекс — самый частый в группе
        index_to = max(set(o.recipient_postal_code for o in orders),
                       key=lambda idx: sum(1 for o in orders if o.recipient_postal_code == idx))

        public_sum = 0
        for order in orders:
            result, _log = await self._pochta.calculate_tariff_public(
                sender_postal_code, order.recipient_postal_code, order.total_weight_grams
            )
            public_sum += result.total_kopecks

        contract_result, _log = await self._pochta.calculate_tariff_contract(
            sender_postal_code, index_to, total_weight
        )

        return {
            "public_total": public_sum,
            "contract_total": contract_result.total_kopecks,
        }

    async def _load_pending_orders(self) -> list[Order]:
        result = await self._session.execute(
            select(Order).where(
                Order.status == "customs_cleared",
                Order.shipment_group_id.is_(None),
            )
        )
        return list(result.scalars().all())

    async def _load_settings(self) -> GroupingSettings:
        result = await self._session.execute(
            select(GroupingSettings).where(GroupingSettings.scope == "global")
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            # Создаём дефолтные настройки
            settings = GroupingSettings(scope="global", scope_name="Глобальные настройки")
            self._session.add(settings)
            await self._session.commit()
        return settings

    @staticmethod
    def _generate_group_number(hub: str) -> str:
        from datetime import date
        import random
        suffix = random.randint(1000, 9999)
        return f"GRP-{date.today().strftime('%Y%m%d')}-{hub.upper()}-{suffix}"

    @staticmethod
    def _generate_track_number(order: Order) -> str:
        from datetime import date
        import random
        suffix = random.randint(10000, 99999)
        return f"OV-{date.today().strftime('%Y%m%d')}-{suffix}"
