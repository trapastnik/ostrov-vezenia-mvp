import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_operator
from app.models.operator import Operator

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
