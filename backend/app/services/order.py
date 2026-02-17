import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory

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
    result = await db.execute(select(Order).where(Order.id == order_id))
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

    history = OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
        changed_by=changed_by,
    )
    db.add(history)

    await db.commit()
    await db.refresh(order)
    return order


async def get_order_with_history(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.status_history), selectinload(Order.shop))
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

    query = query.options(selectinload(Order.shop)).order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    orders = list(result.scalars().all())

    return orders, total
