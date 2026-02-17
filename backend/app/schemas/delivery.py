from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    postal_code: str = Field(..., min_length=5, max_length=6)
    weight_grams: int = Field(..., gt=0)
    total_amount_kopecks: int = Field(..., gt=0)


class CalculateResponse(BaseModel):
    delivery_cost_kopecks: int
    customs_fee_kopecks: int
    total_cost_kopecks: int
    delivery_days_min: int
    delivery_days_max: int
    available: bool
    rejection_reason: str | None = None
