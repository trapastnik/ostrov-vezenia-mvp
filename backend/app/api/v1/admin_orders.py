import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_operator, get_db
from app.models.operator import Operator
from app.schemas.order import (
    ChangeStatusRequest,
    OrderDetailResponse,
    OrderListResponse,
    OrderResponse,
    StatusHistoryEntry,
)
from app.services.order import change_order_status, get_order_with_history, list_orders

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])


@router.get("", response_model=OrderListResponse)
async def list_all_orders(
    status: str | None = Query(None),
    shop_id: UUID | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    orders, total = await list_orders(db, shop_id=shop_id, status_filter=status, page=page, per_page=per_page, search=search)

    items = []
    for o in orders:
        resp = OrderResponse.model_validate(o)
        if o.shop:
            resp.shop_name = o.shop.name
        items.append(resp)

    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, math.ceil(total / per_page)),
    )


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: UUID,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_with_history(db, order_id)
    if not order:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found")

    history = [StatusHistoryEntry.model_validate(h) for h in order.status_history]
    resp = OrderResponse.model_validate(order)
    if order.shop:
        resp.shop_name = order.shop.name
    data = resp.model_dump()
    data["history"] = history
    return OrderDetailResponse(**data)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    body: ChangeStatusRequest,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    order = await change_order_status(db, order_id, body.status, changed_by=operator.id, comment=body.comment)
    return OrderResponse.model_validate(order)
