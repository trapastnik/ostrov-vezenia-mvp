from datetime import datetime
from uuid import UUID

import re

from pydantic import BaseModel, Field, field_validator, model_validator


def _mask_passport(value: str | None) -> str | None:
    """Маскирует паспортные данные: 1234 → **34, 567890 → ****90."""
    if not value:
        return value
    if len(value) <= 2:
        return "*" * len(value)
    return "*" * (len(value) - 2) + value[-2:]


class OrderItem(BaseModel):
    name: str = Field(..., min_length=1)
    sku: str | None = None
    quantity: int = Field(..., gt=0)
    price_kopecks: int = Field(..., gt=0)
    weight_grams: int = Field(..., gt=0)
    # Таможенные поля (заполняются оператором при создании ДТЭГ)
    tn_ved_code: str | None = None  # Код ТН ВЭД ЕАЭС (мин. 6 знаков для ДТЭГ)
    country_of_origin: str | None = None  # ISO 3166-1 alpha-2 (например "CN", "RU")
    brand: str | None = None  # Торговая марка


class RecipientData(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=5, max_length=20)
    email: str | None = None
    address: str = Field(..., min_length=10, max_length=500)
    postal_code: str = Field(..., pattern=r"^\d{6}$")
    # Паспортные данные получателя (обязательно для ДТЭГ)
    passport_series: str = Field(..., pattern=r"^\d{4}$")
    passport_number: str = Field(..., pattern=r"^\d{6}$")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Нормализация и проверка российского телефона."""
        digits = re.sub(r"[\s\-\(\)\+]", "", v)
        if digits.startswith("8") and len(digits) == 11:
            digits = "7" + digits[1:]
        if not re.match(r"^7\d{10}$", digits):
            raise ValueError(
                "Телефон должен быть в формате +7XXXXXXXXXX (российский мобильный)"
            )
        return f"+{digits}"

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Российский почтовый индекс: 6 цифр, не начинается с 0."""
        if v.startswith("0"):
            raise ValueError("Почтовый индекс не может начинаться с 0")
        return v

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Адрес должен содержать что-то осмысленное."""
        if not re.search(r"[а-яА-ЯёЁa-zA-Z]", v):
            raise ValueError("Адрес должен содержать буквы")
        return v.strip()


class OrderCreate(BaseModel):
    external_order_id: str = Field(..., min_length=1)
    recipient: RecipientData
    items: list[OrderItem] = Field(..., min_length=1)


class OrderResponse(BaseModel):
    id: UUID
    external_order_id: str
    shop_name: str | None = None
    status: str
    recipient_name: str
    recipient_phone: str
    recipient_email: str | None
    recipient_address: str
    recipient_postal_code: str
    recipient_passport_series: str | None = None
    recipient_passport_number: str | None = None
    items: list[dict]
    total_amount_kopecks: int
    total_weight_grams: int
    delivery_cost_kopecks: int
    customs_fee_kopecks: int
    track_number: str | None
    batch_id: UUID | None
    customs_declaration_id: UUID | None = None
    customs_declaration_number: str | None = None
    customs_declaration_status: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def mask_passport_data(self):
        self.recipient_passport_series = _mask_passport(self.recipient_passport_series)
        self.recipient_passport_number = _mask_passport(self.recipient_passport_number)
        return self


class OrderStatusResponse(BaseModel):
    id: UUID
    status: str
    track_number: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatusHistoryEntry(BaseModel):
    old_status: str | None
    new_status: str
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderTrackingResponse(BaseModel):
    id: UUID
    status: str
    track_number: str | None
    history: list[StatusHistoryEntry]


class CustomsDeclarationBrief(BaseModel):
    id: UUID
    number: str
    status: str
    orders_count: int
    items_count: int
    total_weight_grams: int
    total_value_kopecks: int
    total_value_usd_cents: int
    sender_name: str
    sender_inn: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderDetailResponse(BaseModel):
    id: UUID
    external_order_id: str
    shop_name: str | None = None
    status: str
    recipient_name: str
    recipient_phone: str
    recipient_email: str | None
    recipient_address: str
    recipient_postal_code: str
    recipient_passport_series: str | None = None
    recipient_passport_number: str | None = None
    items: list[dict]
    total_amount_kopecks: int
    total_weight_grams: int
    delivery_cost_kopecks: int
    customs_fee_kopecks: int
    track_number: str | None
    internal_track_number: str | None = None
    batch_id: UUID | None
    customs_declaration_id: UUID | None = None
    customs_declaration_number: str | None = None
    customs_declaration_status: str | None = None
    customs_declaration: CustomsDeclarationBrief | None = None
    public_tariff_kopecks: int | None = None
    contract_tariff_kopecks: int | None = None
    tariff_savings_kopecks: int | None = None
    tariff_savings_percent: float | None = None
    created_at: datetime
    updated_at: datetime
    history: list[StatusHistoryEntry]

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def mask_passport_data(self):
        self.recipient_passport_series = _mask_passport(self.recipient_passport_series)
        self.recipient_passport_number = _mask_passport(self.recipient_passport_number)
        return self


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ChangeStatusRequest(BaseModel):
    status: str
    comment: str | None = None
