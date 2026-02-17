from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, verify_api_key
from app.models.order import Order
from app.models.shop import Shop
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusResponse,
    OrderTrackingResponse,
    StatusHistoryEntry,
)
from app.services.delivery import DeliveryService
from app.services.order import create_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_new_order(
    body: OrderCreate,
    request: Request,
    shop: Shop = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    total_amount = sum(item.price_kopecks * item.quantity for item in body.items)
    total_weight = sum(item.weight_grams * item.quantity for item in body.items)

    pochta = request.app.state.pochta_client
    service = DeliveryService(pochta)
    calc = await service.calculate(shop, body.recipient.postal_code, total_weight, total_amount)

    if not calc.available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Delivery unavailable: {calc.rejection_reason}")

    order = Order(
        shop_id=shop.id,
        external_order_id=body.external_order_id,
        recipient_name=body.recipient.name,
        recipient_phone=body.recipient.phone,
        recipient_email=body.recipient.email,
        recipient_address=body.recipient.address,
        recipient_postal_code=body.recipient.postal_code,
        items=[item.model_dump() for item in body.items],
        total_amount_kopecks=total_amount,
        total_weight_grams=total_weight,
        delivery_cost_kopecks=calc.delivery_cost_kopecks,
        customs_fee_kopecks=calc.customs_fee_kopecks,
    )

    order = await create_order(db, order)
    return OrderResponse.model_validate(order)


@router.get("/{order_id}/status", response_model=OrderStatusResponse)
async def get_order_status(
    order_id: UUID,
    shop: Shop = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id, Order.shop_id == shop.id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderStatusResponse.model_validate(order)


@router.get("/{order_id}/tracking", response_model=OrderTrackingResponse)
async def get_order_tracking(
    order_id: UUID,
    shop: Shop = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.shop_id == shop.id).options(selectinload(Order.status_history))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    history = [StatusHistoryEntry.model_validate(h) for h in order.status_history]

    return OrderTrackingResponse(
        id=order.id,
        status=order.status,
        track_number=order.track_number,
        history=history,
    )
