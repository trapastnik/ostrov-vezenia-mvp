"""Бизнес-логика таможенных деклараций ДТЭГ (Решение ЕЭК №142)."""
import copy
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.models.company_settings import CompanySettings
from app.models.customs_declaration import CustomsDeclaration
from app.models.order import Order


DECLARATION_ALLOWED_TRANSITIONS = {
    "draft": ["ready"],
    "ready": ["draft", "submitted"],
    "submitted": ["accepted", "rejected"],
    "rejected": ["draft"],
}


def _generate_declaration_number() -> str:
    now = datetime.now(timezone.utc)
    return f"DTEG-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"


async def get_company_settings(db: AsyncSession) -> CompanySettings:
    result = await db.execute(
        select(CompanySettings).where(CompanySettings.scope == "global")
    )
    settings = result.scalar_one_or_none()
    if not settings:
        settings = CompanySettings(scope="global")
        db.add(settings)
        await db.flush()
    return settings


async def create_declaration(
    db: AsyncSession,
    order_ids: list[uuid.UUID],
    goods_location: str | None = None,
    operator_note: str | None = None,
) -> CustomsDeclaration:
    result = await db.execute(select(Order).where(Order.id.in_(order_ids)))
    orders = list(result.scalars().all())

    if len(orders) != len(order_ids):
        raise HTTPException(400, "Некоторые заказы не найдены")

    for order in orders:
        if order.customs_declaration_id is not None:
            raise HTTPException(
                400,
                f"Заказ {order.external_order_id} уже включён в декларацию",
            )

    if len(orders) > 500:
        raise HTTPException(400, "ДТЭГ поддерживает макс. 500 накладных")

    company = await get_company_settings(db)

    total_weight = sum(o.total_weight_grams for o in orders)
    total_value = sum(o.total_amount_kopecks for o in orders)
    total_items = sum(len(o.items) for o in orders)

    total_value_usd_cents = 0
    if company.usd_rate_kopecks > 0:
        total_value_usd_cents = int(total_value * 100 / company.usd_rate_kopecks)

    declaration = CustomsDeclaration(
        number=_generate_declaration_number(),
        orders_count=len(orders),
        items_count=total_items,
        total_weight_grams=total_weight,
        total_value_kopecks=total_value,
        total_value_usd_cents=total_value_usd_cents,
        goods_location=goods_location or company.goods_location or None,
        sender_name=company.company_name,
        sender_address=company.company_address,
        sender_inn=company.company_inn,
        customs_rep_name=company.customs_rep_name or None,
        customs_rep_certificate=company.customs_rep_certificate or None,
        operator_note=operator_note,
    )
    db.add(declaration)
    await db.flush()

    for order in orders:
        order.customs_declaration_id = declaration.id

    await db.commit()
    await db.refresh(declaration)
    return declaration


async def get_declaration(
    db: AsyncSession, declaration_id: uuid.UUID
) -> CustomsDeclaration:
    result = await db.execute(
        select(CustomsDeclaration)
        .where(CustomsDeclaration.id == declaration_id)
        .options(selectinload(CustomsDeclaration.orders))
    )
    declaration = result.scalar_one_or_none()
    if not declaration:
        raise HTTPException(404, "Декларация не найдена")
    return declaration


async def change_declaration_status(
    db: AsyncSession,
    declaration_id: uuid.UUID,
    new_status: str,
    fts_reference: str | None = None,
) -> CustomsDeclaration:
    declaration = await get_declaration(db, declaration_id)

    allowed = DECLARATION_ALLOWED_TRANSITIONS.get(declaration.status, [])
    if new_status not in allowed:
        raise HTTPException(
            400,
            f"Переход {declaration.status} → {new_status} не разрешён. "
            f"Допустимо: {', '.join(allowed)}",
        )

    declaration.status = new_status

    now = datetime.now(timezone.utc)
    if new_status == "submitted":
        declaration.submitted_at = now
    elif new_status == "accepted":
        declaration.accepted_at = now

    if fts_reference:
        declaration.fts_reference = fts_reference

    await db.commit()
    await db.refresh(declaration)
    return declaration


async def delete_declaration(
    db: AsyncSession, declaration_id: uuid.UUID
) -> None:
    declaration = await get_declaration(db, declaration_id)

    if declaration.status != "draft":
        raise HTTPException(400, "Удалить можно только черновик")

    for order in declaration.orders:
        order.customs_declaration_id = None

    await db.delete(declaration)
    await db.commit()


async def validate_declaration(
    db: AsyncSession, declaration_id: uuid.UUID
) -> tuple[bool, list[str]]:
    """Проверить, что у всех товаров заполнены таможенные поля."""
    declaration = await get_declaration(db, declaration_id)
    errors: list[str] = []

    if not declaration.sender_name:
        errors.append("Не заполнен отправитель (настройки компании)")

    for order in declaration.orders:
        for i, item in enumerate(order.items):
            prefix = f"Заказ {order.external_order_id}, товар {i + 1} «{item['name']}»"
            tn_code = item.get("tn_ved_code", "")
            if not tn_code:
                errors.append(f"{prefix}: нет кода ТН ВЭД")
            elif len(tn_code.strip()) < 6:
                errors.append(f"{prefix}: код ТН ВЭД должен быть мин. 6 знаков (ДТЭГ), сейчас: {tn_code}")
            if not item.get("country_of_origin"):
                errors.append(f"{prefix}: нет страны происхождения")

    return len(errors) == 0, errors


async def update_order_items_customs(
    db: AsyncSession,
    order_id: uuid.UUID,
    updates: list[dict],
) -> Order:
    """Обновить таможенные поля товаров в заказе."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Заказ не найден")

    # Deep copy to ensure SQLAlchemy detects changes in JSON field
    items = copy.deepcopy(order.items)
    for upd in updates:
        idx = upd["item_index"]
        if idx < 0 or idx >= len(items):
            raise HTTPException(400, f"Индекс товара {idx} вне диапазона")
        items[idx]["tn_ved_code"] = upd["tn_ved_code"]
        items[idx]["country_of_origin"] = upd["country_of_origin"]
        if upd.get("brand") is not None:
            items[idx]["brand"] = upd["brand"]

    order.items = items
    flag_modified(order, "items")
    await db.commit()
    await db.refresh(order)
    return order
