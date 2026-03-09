import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory
from app.models.tracking_event import TrackingEvent

logger = logging.getLogger(__name__)

# Маппинг статуса заказа → event_type и описание для покупателя
STATUS_TO_TRACKING_EVENT: dict[str, tuple[str, str]] = {
    "accepted": ("order_accepted", "Заказ принят и обрабатывается"),
    "awaiting_pickup": ("order_accepted", "Заказ подтверждён, ожидает забора"),
    "received_warehouse": ("order_validating", "Товар получен на складе"),
    "batch_forming": ("order_validating", "Формирование партии для отправки"),
    "customs_presented": ("order_customs_processing", "Передано на таможенное оформление"),
    "customs_cleared": ("order_customs_cleared", "Таможенное оформление пройдено"),
    "awaiting_carrier": ("order_awaiting_group", "Подготовка к отправке"),
    "shipped": ("last_mile_transferred", "Передано в Почту России"),
    "in_transit": ("last_mile_in_transit", "В пути к получателю"),
    "delivered": ("delivered", "Доставлено получателю"),
    "problem": ("problem", "Возникла проблема с отправлением"),
    "cancelled": ("cancelled", "Заказ отменён"),
}

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "accepted": ["awaiting_pickup", "cancelled"],
    "awaiting_pickup": ["received_warehouse", "cancelled"],
    "received_warehouse": ["batch_forming", "cancelled"],
    "batch_forming": ["customs_presented", "cancelled"],
    "customs_presented": ["customs_cleared", "problem"],
    "customs_cleared": ["awaiting_carrier", "problem"],
    "awaiting_carrier": ["shipped", "problem"],
    "shipped": ["in_transit"],
    "in_transit": ["delivered"],
    "problem": [
        "accepted",
        "awaiting_pickup",
        "received_warehouse",
        "batch_forming",
        "customs_presented",
        "customs_cleared",
        "awaiting_carrier",
        "shipped",
    ],
}


async def create_order(db: AsyncSession, order: Order) -> Order:
    db.add(order)
    await db.flush()

    history = OrderStatusHistory(order_id=order.id, old_status=None, new_status="accepted")
    db.add(history)

    # TrackingEvent: заказ принят
    tracking_event = TrackingEvent(
        order_id=order.id,
        internal_track_number=order.internal_track_number,
        event_type="order_accepted",
        description="Заказ принят и обрабатывается",
    )
    db.add(tracking_event)

    await db.commit()
    await db.refresh(order)
    return order


async def change_order_status(
    db: AsyncSession,
    order_id: uuid.UUID,
    new_status: str,
    changed_by: uuid.UUID | None = None,
    comment: str | None = None,
) -> Order:
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.shop))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    allowed = ALLOWED_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{order.status}' to '{new_status}'",
        )

    old_status = order.status
    order.status = new_status

    # Запись в историю статусов (аудит)
    history = OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
        changed_by=changed_by,
    )
    db.add(history)

    # Создание TrackingEvent для покупателя
    event_info = STATUS_TO_TRACKING_EVENT.get(new_status)
    if event_info:
        event_type, description = event_info
        tracking_event = TrackingEvent(
            order_id=order.id,
            internal_track_number=order.internal_track_number,
            event_type=event_type,
            description=description,
            location=comment,  # Комментарий оператора как контекст
        )
        db.add(tracking_event)

    await db.commit()
    await db.refresh(order)

    # Отправка webhook магазину (в фоне через Celery)
    _enqueue_webhook(order, old_status, new_status)

    return order


def _enqueue_webhook(order: Order, old_status: str, new_status: str) -> None:
    """Ставит Celery-задачу на отправку webhook магазину."""
    try:
        shop = order.shop
        if not shop or not shop.webhook_url:
            return

        from app.workers.tasks_webhook import send_webhook

        payload = {
            "event": "order.status_changed",
            "order_id": str(order.id),
            "external_order_id": order.external_order_id,
            "old_status": old_status,
            "new_status": new_status,
            "track_number": order.track_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        send_webhook.delay(shop.webhook_url, payload, shop.api_key)
        logger.info(
            "Webhook queued: order=%s status=%s→%s url=%s",
            order.id, old_status, new_status, shop.webhook_url,
        )
    except Exception:
        # Вебхук не должен ломать основной процесс
        logger.exception("Failed to enqueue webhook for order %s", order.id)


async def get_order_with_history(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.status_history),
            selectinload(Order.shop),
            selectinload(Order.customs_declaration),
        )
    )
    return result.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    shop_id: uuid.UUID | None = None,
    status_filter: str | None = None,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
) -> tuple[list[Order], int]:
    query = select(Order)
    count_query = select(func.count(Order.id))

    if shop_id:
        query = query.where(Order.shop_id == shop_id)
        count_query = count_query.where(Order.shop_id == shop_id)
    if status_filter:
        query = query.where(Order.status == status_filter)
        count_query = count_query.where(Order.status == status_filter)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            Order.recipient_name.ilike(pattern)
            | Order.external_order_id.ilike(pattern)
            | Order.track_number.ilike(pattern)
        )
        count_query = count_query.where(
            Order.recipient_name.ilike(pattern)
            | Order.external_order_id.ilike(pattern)
            | Order.track_number.ilike(pattern)
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.options(selectinload(Order.shop), selectinload(Order.customs_declaration)).order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    orders = list(result.scalars().all())

    return orders, total
