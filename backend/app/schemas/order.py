from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    name: str
    sku: str | None = None
    quantity: int = Field(..., gt=0)
    price_kopecks: int = Field(..., gt=0)
    weight_grams: int = Field(..., gt=0)


class RecipientData(BaseModel):
    name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=5)
    email: str | None = None
    address: str = Field(..., min_length=5)
    postal_code: str = Field(..., min_length=5, max_length=6)


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
    items: list[dict]
    total_amount_kopecks: int
    total_weight_grams: int
    delivery_cost_kopecks: int
    customs_fee_kopecks: int
    track_number: str | None
    batch_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
    items: list[dict]
    total_amount_kopecks: int
    total_weight_grams: int
    delivery_cost_kopecks: int
    customs_fee_kopecks: int
    track_number: str | None
    batch_id: UUID | None
    created_at: datetime
    updated_at: datetime
    history: list[StatusHistoryEntry]

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ChangeStatusRequest(BaseModel):
    status: str
    comment: str | None = None
