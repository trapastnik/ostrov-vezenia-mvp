from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CustomsDeclarationCreate(BaseModel):
    order_ids: list[UUID] = Field(..., min_length=1, max_length=500)
    goods_location: str | None = None
    operator_note: str | None = None


class CustomsDeclarationUpdate(BaseModel):
    goods_location: str | None = None
    operator_note: str | None = None
    fts_reference: str | None = None


class CustomsDeclarationStatusUpdate(BaseModel):
    status: str  # ready, submitted, accepted, rejected, draft
    fts_reference: str | None = None


class CustomsDeclarationOrderSummary(BaseModel):
    id: UUID
    external_order_id: str
    recipient_name: str
    recipient_address: str
    recipient_postal_code: str
    items: list[dict]
    total_amount_kopecks: int
    total_weight_grams: int
    customs_ready: bool  # True если у всех товаров есть tn_ved_code

    model_config = {"from_attributes": True}


class CustomsDeclarationResponse(BaseModel):
    id: UUID
    number: str
    status: str
    orders_count: int
    items_count: int
    total_weight_grams: int
    total_value_kopecks: int
    total_value_usd_cents: int
    sender_name: str
    sender_address: str
    sender_inn: str
    customs_rep_name: str | None
    customs_rep_certificate: str | None
    goods_location: str | None
    operator_note: str | None
    fts_reference: str | None
    submitted_at: datetime | None
    accepted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomsDeclarationDetailResponse(CustomsDeclarationResponse):
    orders: list[CustomsDeclarationOrderSummary]


class CustomsDeclarationListResponse(BaseModel):
    items: list[CustomsDeclarationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class OrderItemCustomsUpdate(BaseModel):
    item_index: int = Field(..., ge=0)
    tn_ved_code: str = Field("", max_length=10)  # ДТЭГ: мин. 6 знаков
    country_of_origin: str = Field("", max_length=2)
    brand: str | None = None


class OrderItemsBulkCustomsUpdate(BaseModel):
    updates: list[OrderItemCustomsUpdate] = Field(..., min_length=1)
