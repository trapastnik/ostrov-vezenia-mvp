import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_operator, get_db
from app.models.batch import Batch
from app.models.operator import Operator
from app.models.order import Order
from app.schemas.batch import BatchCreate, BatchListResponse, BatchResponse
from app.services.order import change_order_status

router = APIRouter(prefix="/admin/batches", tags=["admin-batches"])


def _generate_batch_number() -> str:
    now = datetime.now(timezone.utc)
    return f"B-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"


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
