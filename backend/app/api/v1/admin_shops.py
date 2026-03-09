import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.security import generate_api_key
from app.models.operator import Operator
from app.models.shop import Shop
from app.schemas.shop import ShopCreate, ShopCreateResponse, ShopResponse, ShopUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/admin/shops", tags=["admin-shops"])


@router.get("", response_model=dict)
async def list_shops(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    operator: Operator = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(func.count(Shop.id)))
    total = total_result.scalar()

    result = await db.execute(select(Shop).order_by(Shop.created_at.desc()).offset((page - 1) * per_page).limit(per_page))
    shops = result.scalars().all()

    return {
        "items": [ShopResponse.model_validate(s) for s in shops],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, math.ceil(total / per_page)),
    }


@router.post("", response_model=ShopCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_shop(
    body: ShopCreate,
    request: Request,
    operator: Operator = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Создание магазина. API-ключ возвращается ТОЛЬКО в этом ответе."""
    existing = await db.execute(select(Shop).where(Shop.domain == body.domain))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Shop with this domain already exists")

    shop = Shop(
        name=body.name,
        domain=body.domain,
        api_key=generate_api_key(),
        webhook_url=body.webhook_url,
        customs_fee_kopecks=body.customs_fee_kopecks,
        sender_postal_code=body.sender_postal_code,
    )
    db.add(shop)
    await log_action(
        db, action="shop.create", resource_type="shop", resource_id=shop.id,
        operator_id=operator.id, details={"name": body.name, "domain": body.domain},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(shop)
    return ShopCreateResponse.model_validate(shop)


@router.get("/{shop_id}", response_model=ShopResponse)
async def get_shop(
    shop_id: UUID,
    operator: Operator = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")
    return ShopResponse.model_validate(shop)


@router.patch("/{shop_id}", response_model=ShopResponse)
async def update_shop(
    shop_id: UUID,
    body: ShopUpdate,
    request: Request,
    operator: Operator = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(shop, key, value)

    await log_action(
        db, action="shop.update", resource_type="shop", resource_id=shop_id,
        operator_id=operator.id, details=update_data,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(shop)
    return ShopResponse.model_validate(shop)


@router.post("/{shop_id}/rotate-key", response_model=ShopCreateResponse)
async def rotate_api_key(
    shop_id: UUID,
    request: Request,
    operator: Operator = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Ротация API-ключа магазина. Новый ключ показывается ОДИН раз."""
    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    shop.api_key = generate_api_key()

    await log_action(
        db, action="shop.rotate_key", resource_type="shop", resource_id=shop_id,
        operator_id=operator.id, details={"shop_name": shop.name},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(shop)
    return ShopCreateResponse.model_validate(shop)
