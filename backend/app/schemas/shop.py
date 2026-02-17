from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ShopCreate(BaseModel):
    name: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=3)
    webhook_url: str | None = None
    customs_fee_kopecks: int = Field(default=15000, ge=0)
    sender_postal_code: str = Field(default="238311", min_length=5, max_length=6)


class ShopUpdate(BaseModel):
    name: str | None = None
    webhook_url: str | None = None
    customs_fee_kopecks: int | None = None
    sender_postal_code: str | None = None
    is_active: bool | None = None


class ShopResponse(BaseModel):
    id: UUID
    name: str
    domain: str
    api_key: str
    webhook_url: str | None
    customs_fee_kopecks: int
    sender_postal_code: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
