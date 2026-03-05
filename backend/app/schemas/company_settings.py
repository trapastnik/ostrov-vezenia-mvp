from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CompanySettingsResponse(BaseModel):
    id: UUID
    company_name: str
    company_address: str
    company_inn: str
    company_kpp: str
    company_postal_code: str
    company_phone: str
    customs_rep_name: str
    customs_rep_certificate: str
    customs_rep_inn: str
    goods_location: str
    usd_rate_kopecks: int
    eur_rate_kopecks: int
    rates_updated_at: datetime | None

    model_config = {"from_attributes": True}


class CompanySettingsUpdate(BaseModel):
    company_name: str | None = None
    company_address: str | None = None
    company_inn: str | None = Field(None, max_length=12)
    company_kpp: str | None = Field(None, max_length=9)
    company_postal_code: str | None = Field(None, min_length=5, max_length=6)
    company_phone: str | None = None
    customs_rep_name: str | None = None
    customs_rep_certificate: str | None = None
    customs_rep_inn: str | None = Field(None, max_length=12)
    goods_location: str | None = None
    usd_rate_kopecks: int | None = Field(None, gt=0)
    eur_rate_kopecks: int | None = Field(None, gt=0)
