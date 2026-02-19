from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.dependencies import get_current_operator
from app.models.operator import Operator

router = APIRouter(prefix="/admin/pochta", tags=["admin-pochta"])


# --- Request schemas ---


class TariffRequest(BaseModel):
    index_from: str = "238311"
    index_to: str
    weight_grams: int


class AddressRequest(BaseModel):
    address: str


class FioRequest(BaseModel):
    fio: str


class PhoneRequest(BaseModel):
    phone: str


# --- Response schemas ---


class TariffResponse(BaseModel):
    cost_kopecks: int
    vat_kopecks: int
    total_kopecks: int
    min_days: int
    max_days: int


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


class FioResponse(BaseModel):
    surname: str
    name: str
    middle_name: str
    quality_code: str


class PhoneResponse(BaseModel):
    country_code: str
    city_code: str
    number: str
    quality_code: str


class BalanceResponse(BaseModel):
    balance_kopecks: int


# --- Endpoints ---


@router.post("/tariff-public", response_model=TariffResponse)
async def tariff_public(
    body: TariffRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result = await pochta.calculate_tariff_public(
            index_from=body.index_from,
            index_to=body.index_to,
            weight_grams=body.weight_grams,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Pochta API error: {e}")
    return TariffResponse(
        cost_kopecks=result.cost_kopecks,
        vat_kopecks=result.vat_kopecks,
        total_kopecks=result.total_kopecks,
        min_days=result.min_days,
        max_days=result.max_days,
    )


@router.post("/tariff-contract", response_model=TariffResponse)
async def tariff_contract(
    body: TariffRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result = await pochta.calculate_tariff_contract(
            index_from=body.index_from,
            index_to=body.index_to,
            weight_grams=body.weight_grams,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Pochta API error: {e}")
    return TariffResponse(
        cost_kopecks=result.cost_kopecks,
        vat_kopecks=result.vat_kopecks,
        total_kopecks=result.total_kopecks,
        min_days=result.min_days,
        max_days=result.max_days,
    )


@router.post("/normalize-address", response_model=AddressResponse)
async def normalize_address(
    body: AddressRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result = await pochta.normalize_address(body.address)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Pochta API error: {e}")
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
    )


@router.post("/normalize-fio", response_model=FioResponse)
async def normalize_fio(
    body: FioRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result = await pochta.normalize_fio(body.fio)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Pochta API error: {e}")
    return FioResponse(
        surname=result.surname,
        name=result.name,
        middle_name=result.middle_name,
        quality_code=result.quality_code,
    )


@router.post("/normalize-phone", response_model=PhoneResponse)
async def normalize_phone(
    body: PhoneRequest,
    request: Request,
    operator: Operator = Depends(get_current_operator),
):
    pochta = request.app.state.pochta_client
    try:
        result = await pochta.normalize_phone(body.phone)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Pochta API error: {e}")
    return PhoneResponse(
        country_code=result.country_code,
        city_code=result.city_code,
        number=result.number,
        quality_code=result.quality_code,
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
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Pochta API error: {e}")
    return BalanceResponse(balance_kopecks=balance)
