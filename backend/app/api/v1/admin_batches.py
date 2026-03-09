import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_operator, get_db
from app.models.batch import Batch
from app.models.operator import Operator
from app.models.order import Order
from app.schemas.batch import (
    BatchCreate,
    BatchDetailResponse,
    BatchListResponse,
    BatchOrderSummary,
    BatchResponse,
    BatchStatusUpdate,
)
from app.services.order import change_order_status

router = APIRouter(prefix="/admin/batches", tags=["admin-batches"])


def _generate_batch_number() -> str:
    import random
    now = datetime.now(timezone.utc)
    suffix = random.randint(100, 999)
    return f"B-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"


BATCH_TRANSITIONS: dict[str, str] = {
    "forming": "customs_presented",
    "customs_presented": "customs_cleared",
    "customs_cleared": "shipped",
}

BATCH_TO_ORDER_STATUS: dict[str, str] = {
    "customs_presented": "customs_presented",
    "customs_cleared": "customs_cleared",
    "shipped": "awaiting_carrier",
}

BATCH_TIMESTAMP_FIELD: dict[str, str] = {
    "customs_presented": "customs_presented_at",
    "customs_cleared": "customs_cleared_at",
    "shipped": "shipped_at",
}


@router.get("", response_model=BatchListResponse)
async def list_batches(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(func.count(Batch.id)))
    total = total_result.scalar()

    result = await db.execute(select(Batch).order_by(Batch.created_at.desc()).offset((page - 1) * per_page).limit(per_page))
    batches = result.scalars().all()

    return BatchListResponse(
        items=[BatchResponse.model_validate(b) for b in batches],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, math.ceil(total / per_page)),
    )


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    body: BatchCreate,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id.in_(body.order_ids)))
    orders = list(result.scalars().all())

    if len(orders) != len(body.order_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some orders not found")

    for order in orders:
        if order.status != "received_warehouse":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order {order.external_order_id} is not in 'received_warehouse' status",
            )

    batch = Batch(
        number=_generate_batch_number(),
        orders_count=len(orders),
        total_weight_grams=sum(o.total_weight_grams for o in orders),
    )
    db.add(batch)
    await db.flush()

    for order in orders:
        order.batch_id = batch.id
        await change_order_status(db, order.id, "batch_forming", changed_by=operator.id, comment=f"Batch {batch.number}")

    await db.commit()
    await db.refresh(batch)
    return BatchResponse.model_validate(batch)


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def get_batch(
    batch_id: UUID,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id).options(selectinload(Batch.orders))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    orders_out = [
        BatchOrderSummary(
            id=o.id,
            external_order_id=o.external_order_id,
            recipient_name=o.recipient_name,
            recipient_address=o.recipient_address,
            recipient_postal_code=o.recipient_postal_code,
            items=o.items or [],
            total_amount_kopecks=o.total_amount_kopecks,
            total_weight_grams=o.total_weight_grams,
            status=o.status,
        )
        for o in batch.orders
    ]

    return BatchDetailResponse(
        **BatchResponse.model_validate(batch).model_dump(),
        orders=orders_out,
    )


@router.patch("/{batch_id}/status", response_model=BatchResponse)
async def update_batch_status(
    batch_id: UUID,
    body: BatchStatusUpdate,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id).options(selectinload(Batch.orders))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    allowed_next = BATCH_TRANSITIONS.get(batch.status)
    if body.status != allowed_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition batch from '{batch.status}' to '{body.status}'",
        )

    # Update batch status + timestamp
    batch.status = body.status
    ts_field = BATCH_TIMESTAMP_FIELD.get(body.status)
    if ts_field:
        setattr(batch, ts_field, datetime.now(timezone.utc))

    await db.flush()

    # Cascade to orders
    order_target = BATCH_TO_ORDER_STATUS.get(body.status)
    if order_target:
        for order in batch.orders:
            await change_order_status(
                db,
                order.id,
                order_target,
                changed_by=operator.id,
                comment=f"Партия {batch.number}: {body.status}",
            )

    await db.commit()
    await db.refresh(batch)
    return BatchResponse.model_validate(batch)
