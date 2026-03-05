from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_operator, get_db
from app.models.operator import Operator
from app.schemas.company_settings import CompanySettingsResponse, CompanySettingsUpdate
from app.services.customs_declaration import get_company_settings

router = APIRouter(prefix="/admin/company", tags=["admin-company"])


@router.get("/settings", response_model=CompanySettingsResponse)
async def get_settings(
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    settings = await get_company_settings(db)
    await db.commit()  # commit auto-created row if new
    return CompanySettingsResponse.model_validate(settings)


@router.patch("/settings", response_model=CompanySettingsResponse)
async def update_settings(
    body: CompanySettingsUpdate,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    settings = await get_company_settings(db)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return CompanySettingsResponse.model_validate(settings)


@router.post("/settings/update-rates", response_model=CompanySettingsResponse)
async def update_rates(
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    """Обновить курсы USD/EUR из API ЦБ РФ."""
    from app.services.cbr_rates import update_company_rates

    try:
        settings = await update_company_rates(db)
    except Exception as e:
        raise HTTPException(502, f"Ошибка загрузки курсов ЦБ РФ: {e}")

    return CompanySettingsResponse.model_validate(settings)
