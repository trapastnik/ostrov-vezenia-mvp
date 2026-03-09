"""Бизнес-логика таможенных деклараций ДТЭГ (Решение ЕЭК №142)."""
import copy
import secrets
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

# Запрещённые / подакцизные товары (по префиксам ТН ВЭД)
# Алкоголь, табак, спирт — не допускаются к перемещению по Калининградскому эксперименту
PROHIBITED_TN_VED_PREFIXES = [
    "2203",  # Пиво солодовое
    "2204",  # Вина виноградные
    "2205",  # Вермуты
    "2206",  # Напитки сброженные прочие
    "2207",  # Спирт этиловый
    "2208",  # Спиртовые настойки, ликёры
    "2402",  # Сигары, сигариллы, сигареты
    "2403",  # Прочий табак
    "3003",  # Лекарственные средства (некоторые)
    "3004",  # Лекарственные средства расфасованные (некоторые)
]

# Максимальная стоимость заказа в EUR (жёсткий лимит эксперимента)
MAX_ORDER_VALUE_EUR = 200
# Максимальный вес заказа в граммах
MAX_ORDER_WEIGHT_GRAMS = 31000


def _generate_declaration_number() -> str:
    now = datetime.now(timezone.utc)
    suffix = secrets.token_hex(4).upper()
    return f"DTEG-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"


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

    # Проверка лимитов для каждого заказа (предупреждения, не блокирующие)
    warnings: list[str] = []
    eur_rate = company.eur_rate_kopecks or 10500  # fallback

    for order in orders:
        # Проверка стоимости в EUR
        order_value_eur = order.total_amount_kopecks / eur_rate
        if order_value_eur > MAX_ORDER_VALUE_EUR:
            warnings.append(
                f"Заказ {order.external_order_id}: стоимость {order_value_eur:.2f} EUR "
                f"превышает лимит {MAX_ORDER_VALUE_EUR} EUR"
            )

        # Проверка веса
        if order.total_weight_grams > MAX_ORDER_WEIGHT_GRAMS:
            warnings.append(
                f"Заказ {order.external_order_id}: вес {order.total_weight_grams}г "
                f"превышает лимит {MAX_ORDER_WEIGHT_GRAMS}г"
            )

    total_weight = sum(o.total_weight_grams for o in orders)
    total_value = sum(o.total_amount_kopecks for o in orders)
    total_items = sum(len(o.items) for o in orders)

    total_value_usd_cents = 0
    if company.usd_rate_kopecks > 0:
        total_value_usd_cents = int(total_value * 100 / company.usd_rate_kopecks)

    total_value_eur_cents = 0
    if eur_rate > 0:
        total_value_eur_cents = int(total_value * 100 / eur_rate)

    # Объединяем примечание оператора с предупреждениями
    note_parts = []
    if operator_note:
        note_parts.append(operator_note)
    if warnings:
        note_parts.append("ПРЕДУПРЕЖДЕНИЯ: " + "; ".join(warnings))
    final_note = "\n".join(note_parts) if note_parts else None

    declaration = CustomsDeclaration(
        number=_generate_declaration_number(),
        orders_count=len(orders),
        items_count=total_items,
        total_weight_grams=total_weight,
        total_value_kopecks=total_value,
        total_value_usd_cents=total_value_usd_cents,
        total_value_eur_cents=total_value_eur_cents,
        goods_location=goods_location or company.goods_location or None,
        sender_name=company.company_name,
        sender_address=company.company_address,
        sender_inn=company.company_inn,
        customs_rep_name=company.customs_rep_name or None,
        customs_rep_certificate=company.customs_rep_certificate or None,
        operator_note=final_note,
    )
    db.add(declaration)
    await db.flush()

    for order in orders:
        order.customs_declaration_id = declaration.id

    await db.commit()
    await db.refresh(declaration)
    return declaration


async def get_declaration(
    db: AsyncSession, declaration_id: uuid.UUID, *, for_update: bool = False
) -> CustomsDeclaration:
    stmt = (
        select(CustomsDeclaration)
        .where(CustomsDeclaration.id == declaration_id)
        .options(selectinload(CustomsDeclaration.orders))
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
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
    declaration = await get_declaration(db, declaration_id, for_update=True)

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


def _is_prohibited_tn_ved(code: str) -> bool:
    """Проверить, является ли код ТН ВЭД запрещённым/подакцизным."""
    for prefix in PROHIBITED_TN_VED_PREFIXES:
        if code.startswith(prefix):
            return True
    return False


async def validate_declaration(
    db: AsyncSession, declaration_id: uuid.UUID
) -> tuple[bool, list[str]]:
    """Проверить, что у всех товаров заполнены таможенные поля и соблюдены лимиты."""
    declaration = await get_declaration(db, declaration_id)
    company = await get_company_settings(db)
    errors: list[str] = []

    if not declaration.sender_name:
        errors.append("Не заполнен отправитель (настройки компании)")

    eur_rate = company.eur_rate_kopecks or 10500

    for order in declaration.orders:
        order_prefix = f"Заказ {order.external_order_id}"

        # Паспортные данные получателя
        if not order.recipient_passport_series or not order.recipient_passport_number:
            errors.append(f"{order_prefix}: нет паспортных данных получателя (обязательно для ДТЭГ)")

        # Лимит стоимости 200 EUR
        order_value_eur = order.total_amount_kopecks / eur_rate
        if order_value_eur > MAX_ORDER_VALUE_EUR:
            errors.append(
                f"{order_prefix}: стоимость {order_value_eur:.2f} EUR "
                f"превышает лимит {MAX_ORDER_VALUE_EUR} EUR"
            )

        # Лимит веса 31 кг
        if order.total_weight_grams > MAX_ORDER_WEIGHT_GRAMS:
            errors.append(
                f"{order_prefix}: вес {order.total_weight_grams / 1000:.1f} кг "
                f"превышает лимит {MAX_ORDER_WEIGHT_GRAMS / 1000:.0f} кг"
            )

        # Проверка товаров
        for i, item in enumerate(order.items):
            prefix = f"{order_prefix}, товар {i + 1} «{item['name']}»"
            tn_code = item.get("tn_ved_code", "")
            if not tn_code:
                errors.append(f"{prefix}: нет кода ТН ВЭД")
            elif len(tn_code.strip()) < 6:
                errors.append(f"{prefix}: код ТН ВЭД должен быть мин. 6 знаков (ДТЭГ), сейчас: {tn_code}")
            elif _is_prohibited_tn_ved(tn_code.strip()):
                errors.append(f"{prefix}: код ТН ВЭД {tn_code} — запрещённый/подакцизный товар")

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
