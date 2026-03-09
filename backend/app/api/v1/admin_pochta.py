import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session
from app.core.dependencies import get_current_operator
from app.models.batch import Batch
from app.models.operator import Operator
from app.models.order import Order
from app.services.order import change_order_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/pochta", tags=["admin-pochta"])


# --- Request schemas ---


class TariffRequest(BaseModel):
    index_from: str = Field("238311", pattern=r"^\d{6}$")
    index_to: str = Field(..., pattern=r"^\d{6}$")
    weight_grams: int = Field(..., gt=0, le=30000)


class AddressRequest(BaseModel):
    address: str = Field(..., min_length=5, max_length=500)


class FioRequest(BaseModel):
    fio: str = Field(..., min_length=2, max_length=200)


class PhoneRequest(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20)


# --- Response schemas ---


class PochtaHttpLog(BaseModel):
    method: str
    url: str
    headers: dict
    request_body: list | dict | None
    response_status: int
    response_body: list | dict
    duration_ms: int


class TariffResponse(BaseModel):
    cost_kopecks: int
    vat_kopecks: int
    total_kopecks: int
    min_days: int
    max_days: int
    pochta_log: list[PochtaHttpLog] = []


class AddressResponse(BaseModel):
    index: str
    region: str
    place: str
    street: str
    house: str
    room: str
    quality_code: str
    validation_code: str
    is_valid: bool
    pochta_log: list[PochtaHttpLog] = []


class FioResponse(BaseModel):
    surname: str
    name: str
    middle_name: str
    quality_code: str
    pochta_log: list[PochtaHttpLog] = []


class PhoneResponse(BaseModel):
    country_code: str
    city_code: str
    number: str
    quality_code: str
    pochta_log: list[PochtaHttpLog] = []


class BalanceResponse(BaseModel):
    balance_kopecks: int | None
    available: bool
    message: str | None = None


class TariffCompareResponse(BaseModel):
    public_cost_kopecks: int
    public_vat_kopecks: int
    public_total_kopecks: int
    contract_cost_kopecks: int
    contract_vat_kopecks: int
    contract_total_kopecks: int
    savings_kopecks: int
    savings_percent: float
    min_days: int
    max_days: int
    contract_available: bool
    contract_error: str | None
    pochta_log: list[PochtaHttpLog] = []


# --- Endpoints ---


@router.post("/tariff-public", response_model=TariffResponse)
async def tariff_public(
    body: TariffRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result, log = await pochta.calculate_tariff_public(
            index_from=body.index_from,
            index_to=body.index_to,
            weight_grams=body.weight_grams,
        )
    except Exception as e:
        logger.error(f"Pochta API error in tariff_public: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Pochta API unavailable")
    return TariffResponse(
        cost_kopecks=result.cost_kopecks,
        vat_kopecks=result.vat_kopecks,
        total_kopecks=result.total_kopecks,
        min_days=result.min_days,
        max_days=result.max_days,
        pochta_log=[PochtaHttpLog(**vars(log))],
    )


@router.post("/tariff-contract", response_model=TariffResponse)
async def tariff_contract(
    body: TariffRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result, log = await pochta.calculate_tariff_contract(
            index_from=body.index_from,
            index_to=body.index_to,
            weight_grams=body.weight_grams,
        )
    except Exception as e:
        logger.error(f"Pochta API error in tariff_contract: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Pochta API unavailable")
    return TariffResponse(
        cost_kopecks=result.cost_kopecks,
        vat_kopecks=result.vat_kopecks,
        total_kopecks=result.total_kopecks,
        min_days=result.min_days,
        max_days=result.max_days,
        pochta_log=[PochtaHttpLog(**vars(log))],
    )


@router.post("/normalize-address", response_model=AddressResponse)
async def normalize_address(
    body: AddressRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result, log = await pochta.normalize_address(body.address)
    except Exception as e:
        logger.error(f"Pochta API error in normalize_address: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Pochta API unavailable")
    return AddressResponse(
        index=result.index,
        region=result.region,
        place=result.place,
        street=result.street,
        house=result.house,
        room=result.room,
        quality_code=result.quality_code,
        validation_code=result.validation_code,
        is_valid=result.is_valid,
        pochta_log=[PochtaHttpLog(**vars(log))],
    )


@router.post("/normalize-fio", response_model=FioResponse)
async def normalize_fio(
    body: FioRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result, log = await pochta.normalize_fio(body.fio)
    except Exception as e:
        logger.error(f"Pochta API error in normalize_fio: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Pochta API unavailable")
    return FioResponse(
        surname=result.surname,
        name=result.name,
        middle_name=result.middle_name,
        quality_code=result.quality_code,
        pochta_log=[PochtaHttpLog(**vars(log))],
    )


@router.post("/normalize-phone", response_model=PhoneResponse)
async def normalize_phone(
    body: PhoneRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result, log = await pochta.normalize_phone(body.phone)
    except Exception as e:
        logger.error(f"Pochta API error in normalize_phone: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Pochta API unavailable")
    return PhoneResponse(
        country_code=result.country_code,
        city_code=result.city_code,
        number=result.number,
        quality_code=result.quality_code,
        pochta_log=[PochtaHttpLog(**vars(log))],
    )


@router.post("/tariff-compare", response_model=TariffCompareResponse)
async def tariff_compare(
    body: TariffRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result, logs = await pochta.compare_tariffs(
            index_from=body.index_from,
            index_to=body.index_to,
            weight_grams=body.weight_grams,
        )
    except Exception as e:
        logger.error(f"Pochta API error in tariff_compare: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Pochta API unavailable")
    return TariffCompareResponse(
        public_cost_kopecks=result.public_cost_kopecks,
        public_vat_kopecks=result.public_vat_kopecks,
        public_total_kopecks=result.public_total_kopecks,
        contract_cost_kopecks=result.contract_cost_kopecks,
        contract_vat_kopecks=result.contract_vat_kopecks,
        contract_total_kopecks=result.contract_total_kopecks,
        savings_kopecks=result.savings_kopecks,
        savings_percent=result.savings_percent,
        min_days=result.min_days,
        max_days=result.max_days,
        contract_available=result.contract_available,
        contract_error=result.contract_error,
        pochta_log=[PochtaHttpLog(**vars(log)) for log in logs],
    )


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        balance = await pochta.get_balance()
    except Exception as e:
        logger.error(f"Pochta API error in get_balance: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Pochta API unavailable")
    if balance is None:
        return BalanceResponse(
            balance_kopecks=None,
            available=False,
            message="Баланс недоступен: для этого аккаунта не подключён договор на отправку. Обратитесь на otpravka.pochta.ru",
        )
    return BalanceResponse(balance_kopecks=balance, available=True)


# --- Shipment helpers ---


async def _transition_to_shipped(
    session, order_id: uuid.UUID, operator_id: uuid.UUID, barcode: str
) -> None:
    """Переводит заказ в статус shipped, проходя через промежуточные статусы."""
    # Перечитываем заказ, чтобы узнать текущий статус
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.status == "shipped":
        return

    # customs_cleared → awaiting_carrier → shipped
    if order.status == "customs_cleared":
        await change_order_status(
            session, order_id, "awaiting_carrier",
            changed_by=operator_id,
            comment="Подготовка к отправке (Почта России)",
        )

    # awaiting_carrier → shipped
    result2 = await session.execute(select(Order).where(Order.id == order_id))
    order2 = result2.scalar_one_or_none()
    if order2 and order2.status == "awaiting_carrier":
        await change_order_status(
            session, order_id, "shipped",
            changed_by=operator_id,
            comment=f"Создано отправление ПР: {barcode}",
        )


# --- Shipment creation ---


class ShipmentRequest(BaseModel):
    order_id: str


class ShipmentResponse(BaseModel):
    order_id: str
    pochta_id: int
    barcode: str  # Трек-номер ПР
    message: str


class BatchShipmentsResponse(BaseModel):
    created: list[ShipmentResponse]
    errors: list[dict]
    total: int
    success_count: int
    error_count: int


@router.post("/create-shipment", response_model=ShipmentResponse)
async def create_shipment(
    body: ShipmentRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    """Создать отправление в Почте России для одного заказа."""
    pochta = request.app.state.pochta_client

    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == uuid.UUID(body.order_id))
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.track_number:
            raise HTTPException(status_code=400, detail=f"Заказ уже имеет трек-номер: {order.track_number}")

        # Проверяем статус — отправление можно создать после таможни
        allowed_statuses = {"customs_cleared", "awaiting_carrier"}
        if order.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя создать отправление для статуса «{order.status}». Нужен: customs_cleared или awaiting_carrier",
            )

        try:
            shipment_result, log = await pochta.create_shipment(
                recipient_name=order.recipient_name,
                recipient_address=order.recipient_address,
                recipient_postal_code=order.recipient_postal_code,
                recipient_phone=order.recipient_phone,
                weight_grams=order.total_weight_grams,
                order_num=order.external_order_id,
                declared_value_kopecks=order.total_amount_kopecks,
            )
        except Exception as e:
            logger.error("Pochta create_shipment error: %s", e, exc_info=True)
            raise HTTPException(status_code=502, detail=f"Ошибка Почты России: {e}")

        # Сохраняем трек-номер
        order.track_number = shipment_result.barcode
        await session.commit()

        # Переводим статус: customs_cleared → awaiting_carrier → shipped
        try:
            await _transition_to_shipped(session, order.id, operator.id, shipment_result.barcode)
        except Exception:
            logger.warning("Could not change status to shipped for order %s", order.id)

    return ShipmentResponse(
        order_id=str(order.id),
        pochta_id=shipment_result.pochta_id,
        barcode=shipment_result.barcode,
        message=f"Отправление создано, трек: {shipment_result.barcode}",
    )


@router.post("/batch/{batch_id}/create-shipments", response_model=BatchShipmentsResponse)
async def create_batch_shipments(
    batch_id: str,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    """Массовое создание отправлений для всех заказов в партии."""
    pochta = request.app.state.pochta_client

    async with async_session() as session:
        result = await session.execute(
            select(Batch)
            .where(Batch.id == uuid.UUID(batch_id))
            .options(selectinload(Batch.orders))
        )
        batch = result.scalar_one_or_none()

        if not batch:
            raise HTTPException(status_code=404, detail="Партия не найдена")

        created: list[ShipmentResponse] = []
        errors: list[dict] = []

        for order in batch.orders:
            # Пропускаем заказы с уже присвоенным трек-номером
            if order.track_number:
                continue

            # Пропускаем заказы в неподходящем статусе
            if order.status not in {"customs_cleared", "awaiting_carrier"}:
                errors.append({
                    "order_id": str(order.id),
                    "external_order_id": order.external_order_id,
                    "error": f"Неподходящий статус: {order.status}",
                })
                continue

            try:
                shipment_result, log = await pochta.create_shipment(
                    recipient_name=order.recipient_name,
                    recipient_address=order.recipient_address,
                    recipient_postal_code=order.recipient_postal_code,
                    recipient_phone=order.recipient_phone,
                    weight_grams=order.total_weight_grams,
                    order_num=order.external_order_id,
                    declared_value_kopecks=order.total_amount_kopecks,
                )

                order.track_number = shipment_result.barcode
                await session.commit()

                # Переводим статус: customs_cleared → awaiting_carrier → shipped
                try:
                    await _transition_to_shipped(session, order.id, operator.id, shipment_result.barcode)
                except Exception:
                    pass

                created.append(ShipmentResponse(
                    order_id=str(order.id),
                    pochta_id=shipment_result.pochta_id,
                    barcode=shipment_result.barcode,
                    message=f"Трек: {shipment_result.barcode}",
                ))
            except Exception as e:
                logger.error("Shipment creation failed for order %s: %s", order.id, e)
                errors.append({
                    "order_id": str(order.id),
                    "external_order_id": order.external_order_id,
                    "error": str(e),
                })

    return BatchShipmentsResponse(
        created=created,
        errors=errors,
        total=len(created) + len(errors),
        success_count=len(created),
        error_count=len(errors),
    )
