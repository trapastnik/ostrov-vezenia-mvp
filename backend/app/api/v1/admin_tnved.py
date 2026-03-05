"""API для поиска кодов ТН ВЭД ЕАЭС."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_operator, get_db
from app.models.operator import Operator
from app.models.tn_ved_code import TnVedCode
from app.schemas.tn_ved import TnVedDetailResponse, TnVedSearchResponse, TnVedSearchResult

router = APIRouter(prefix="/admin/tnved", tags=["admin-tnved"])


@router.get("/search", response_model=TnVedSearchResponse)
async def search_tn_ved(
    q: str = Query(..., min_length=2, description="Поисковый запрос (код или наименование)"),
    limit: int = Query(20, ge=1, le=100),
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    """Поиск по справочнику ТН ВЭД: по коду (начало) или по наименованию (подстрока)."""
    q_stripped = q.strip()

    # Если запрос — цифры, ищем по префиксу кода
    if q_stripped.isdigit():
        stmt = (
            select(TnVedCode)
            .where(TnVedCode.code.startswith(q_stripped))
            .order_by(TnVedCode.code)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(TnVedCode)
            .where(TnVedCode.code.startswith(q_stripped))
        )
    else:
        # Поиск по наименованию (LIKE, регистронезависимый)
        pattern = f"%{q_stripped}%"
        stmt = (
            select(TnVedCode)
            .where(
                or_(
                    TnVedCode.name.ilike(pattern),
                    TnVedCode.code.startswith(q_stripped),
                )
            )
            .order_by(TnVedCode.level.desc(), TnVedCode.code)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(TnVedCode)
            .where(
                or_(
                    TnVedCode.name.ilike(pattern),
                    TnVedCode.code.startswith(q_stripped),
                )
            )
        )

    result = await db.execute(stmt)
    items = result.scalars().all()

    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    return TnVedSearchResponse(
        items=[TnVedSearchResult.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{code}", response_model=TnVedDetailResponse)
async def get_tn_ved_code(
    code: str,
    operator: Operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db),
):
    """Получить код ТН ВЭД с иерархией (от корня до кода)."""
    result = await db.execute(
        select(TnVedCode).where(TnVedCode.code == code)
    )
    tn_ved = result.scalar_one_or_none()
    if not tn_ved:
        raise HTTPException(404, f"Код ТН ВЭД {code} не найден")

    # Собираем иерархию: от текущего кода вверх по parent_code
    hierarchy: list[TnVedSearchResult] = []
    current = tn_ved
    visited = set()
    while current and current.parent_code and current.parent_code not in visited:
        visited.add(current.parent_code)
        parent_result = await db.execute(
            select(TnVedCode).where(TnVedCode.code == current.parent_code)
        )
        parent = parent_result.scalar_one_or_none()
        if parent:
            hierarchy.insert(0, TnVedSearchResult.model_validate(parent))
            current = parent
        else:
            break

    response = TnVedDetailResponse.model_validate(tn_ved)
    response.hierarchy = hierarchy
    return response
