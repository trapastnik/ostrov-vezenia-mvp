from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    order_ids: list[UUID] = Field(..., min_length=1)
    goods_location: str | None = None  # Местоположение товаров для ДТЭГ


class BatchResponse(BaseModel):
    id: UUID
    number: str
    status: str
    orders_count: int
    total_weight_grams: int
    customs_declaration_id: UUID | None = None
    customs_declaration_number: str | None = None
    customs_declaration_status: str | None = None
    created_at: datetime
    customs_presented_at: datetime | None
    customs_cleared_at: datetime | None
    shipped_at: datetime | None

    model_config = {"from_attributes": True}


class BatchListResponse(BaseModel):
    items: list[BatchResponse]
    total: int
    page: int
    per_page: int
    pages: int


class BatchStatusUpdate(BaseModel):
    status: str


class BatchOrderSummary(BaseModel):
    id: UUID
    external_order_id: str
    recipient_name: str
    recipient_address: str
    recipient_postal_code: str
    items: list[dict]
    total_amount_kopecks: int
    total_weight_grams: int
    status: str

    model_config = {"from_attributes": True}


class BatchDetailResponse(BatchResponse):
    orders: list[BatchOrderSummary]
