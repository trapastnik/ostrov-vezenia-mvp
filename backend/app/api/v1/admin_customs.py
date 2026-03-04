import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_operator, get_db
from app.models.customs_declaration import CustomsDeclaration
from app.models.operator import Operator
from app.schemas.customs_declaration import (
    CustomsDeclarationCreate,
    CustomsDeclarationDetailResponse,
    CustomsDeclarationListResponse,
    CustomsDeclarationOrderSummary,
    CustomsDeclarationResponse,
    CustomsDeclarationStatusUpdate,
    OrderItemsBulkCustomsUpdate,
)
from app.services.customs_declaration import (
    change_declaration_status,
    create_declaration,
    delete_declaration,
    get_declaration,
    update_order_items_customs,
    validate_declaration,
)
from app.services.customs_export import generate_csv, generate_pdf

router = APIRouter(prefix="/admin/customs", tags=["admin-customs"])


@router.get("/declarations", response_model=CustomsDeclarationListResponse)
async def list_declarations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    q = select(CustomsDeclaration)
    if status_filter:
        q = q.where(CustomsDeclaration.status == status_filter)

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    q = q.order_by(CustomsDeclaration.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    declarations = list(result.scalars().all())

    return CustomsDeclarationListResponse(
        items=[CustomsDeclarationResponse.model_validate(d) for d in declarations],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, math.ceil(total / per_page)),
    )


@router.post(
    "/declarations",
    response_model=CustomsDeclarationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_declaration_endpoint(
    body: CustomsDeclarationCreate,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    declaration = await create_declaration(
        db, body.order_ids, body.goods_location, body.operator_note
    )
    return CustomsDeclarationResponse.model_validate(declaration)


@router.get("/declarations/{declaration_id}", response_model=CustomsDeclarationDetailResponse)
async def get_declaration_endpoint(
    declaration_id: UUID,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    declaration = await get_declaration(db, declaration_id)

    orders_out = []
    for order in declaration.orders:
        all_items_ready = all(
            item.get("tn_ved_code") and item.get("country_of_origin")
            for item in order.items
        )
        orders_out.append(CustomsDeclarationOrderSummary(
            id=order.id,
            external_order_id=order.external_order_id,
            recipient_name=order.recipient_name,
            recipient_address=order.recipient_address,
            recipient_postal_code=order.recipient_postal_code,
            items=order.items,
            total_amount_kopecks=order.total_amount_kopecks,
            total_weight_grams=order.total_weight_grams,
            customs_ready=all_items_ready,
        ))

    resp = CustomsDeclarationResponse.model_validate(declaration)
    return CustomsDeclarationDetailResponse(
        **resp.model_dump(),
        orders=orders_out,
    )


@router.patch("/declarations/{declaration_id}/status", response_model=CustomsDeclarationResponse)
async def update_status_endpoint(
    declaration_id: UUID,
    body: CustomsDeclarationStatusUpdate,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    declaration = await change_declaration_status(
        db, declaration_id, body.status, body.fts_reference
    )
    return CustomsDeclarationResponse.model_validate(declaration)


@router.post("/declarations/{declaration_id}/validate")
async def validate_declaration_endpoint(
    declaration_id: UUID,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    is_valid, errors = await validate_declaration(db, declaration_id)
    return {"valid": is_valid, "errors": errors}


@router.delete("/declarations/{declaration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_declaration_endpoint(
    declaration_id: UUID,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    await delete_declaration(db, declaration_id)


@router.get("/declarations/{declaration_id}/export/csv")
async def export_csv_endpoint(
    declaration_id: UUID,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    csv_buffer = await generate_csv(db, declaration_id)
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="ptd-eg-{declaration_id}.csv"',
        },
    )


@router.get("/declarations/{declaration_id}/export/pdf")
async def export_pdf_endpoint(
    declaration_id: UUID,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    pdf_buffer = await generate_pdf(db, declaration_id)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ptd-eg-{declaration_id}.pdf"',
        },
    )


@router.patch("/orders/{order_id}/items")
async def update_order_items_customs_endpoint(
    order_id: UUID,
    body: OrderItemsBulkCustomsUpdate,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    order = await update_order_items_customs(
        db, order_id, [u.model_dump() for u in body.updates]
    )
    return {"ok": True, "items": order.items}
