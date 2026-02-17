from fastapi import APIRouter, Depends, Request

from app.core.dependencies import verify_api_key
from app.models.shop import Shop
from app.schemas.delivery import CalculateRequest, CalculateResponse
from app.services.delivery import DeliveryService

router = APIRouter(prefix="/delivery", tags=["delivery"])


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_delivery(
    body: CalculateRequest,
    request: Request,
    shop: Shop = Depends(verify_api_key),
):
    pochta = request.app.state.pochta_client
    service = DeliveryService(pochta)

    result = await service.calculate(
        shop=shop,
        postal_code=body.postal_code,
        weight_grams=body.weight_grams,
        total_amount_kopecks=body.total_amount_kopecks,
    )

    return CalculateResponse(
        delivery_cost_kopecks=result.delivery_cost_kopecks,
        customs_fee_kopecks=result.customs_fee_kopecks,
        total_cost_kopecks=result.total_cost_kopecks,
        delivery_days_min=result.delivery_days_min,
        delivery_days_max=result.delivery_days_max,
        available=result.available,
        rejection_reason=result.rejection_reason,
    )
