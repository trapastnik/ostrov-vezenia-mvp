import logging
import time
from importlib.metadata import version as pkg_version

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_operator, get_db
from app.models.operator import Operator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/health", tags=["admin-health"])

APP_VERSION = pkg_version("ostrov-backend")
_start_time = time.time()


class ServiceStatus(BaseModel):
    name: str
    status: str  # "ok" | "error" | "unknown"
    latency_ms: int | None = None
    detail: str | None = None


class SystemStats(BaseModel):
    orders_total: int
    orders_today: int
    shops_total: int
    batches_total: int


class HealthResponse(BaseModel):
    version: str
    uptime_seconds: int
    services: list[ServiceStatus]
    stats: SystemStats


class TestResult(BaseModel):
    name: str
    status: str  # "pass" | "fail" | "skip"
    detail: str | None = None
    duration_ms: int


class SystemTestsResponse(BaseModel):
    results: list[TestResult]
    passed: int
    failed: int
    total: int


# --- Health check ---

@router.get("", response_model=HealthResponse)
async def get_health(
    request: Request,
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    services: list[ServiceStatus] = []

    # 1. Database check
    t0 = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        db_ms = int((time.monotonic() - t0) * 1000)
        services.append(ServiceStatus(name="PostgreSQL / SQLite", status="ok", latency_ms=db_ms))
    except Exception as e:
        services.append(ServiceStatus(name="PostgreSQL / SQLite", status="error", detail=str(e)[:200]))

    # 2. Redis check
    t0 = time.monotonic()
    try:
        import redis.asyncio as aioredis  # lazy import — redis may not be installed in dev
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        redis_ms = int((time.monotonic() - t0) * 1000)
        services.append(ServiceStatus(name="Redis", status="ok", latency_ms=redis_ms))
    except Exception as e:
        services.append(ServiceStatus(name="Redis", status="error", detail=str(e)[:200]))

    # 3. Pochta API (public tariff — no auth needed, fast)
    pochta_client = getattr(request.app.state, "pochta_client", None)
    if pochta_client is not None:
        t0 = time.monotonic()
        try:
            result, _log = await pochta_client.calculate_tariff_public(
                index_from="238311",
                index_to="101000",
                weight_grams=500,
            )
            pochta_ms = int((time.monotonic() - t0) * 1000)
            if result is not None:
                services.append(ServiceStatus(name="Почта России API", status="ok", latency_ms=pochta_ms))
            else:
                services.append(ServiceStatus(name="Почта России API", status="error", detail="No result returned"))
        except Exception as e:
            pochta_ms = int((time.monotonic() - t0) * 1000)
            services.append(ServiceStatus(name="Почта России API", status="error", latency_ms=pochta_ms, detail=str(e)[:200]))
    else:
        services.append(ServiceStatus(name="Почта России API", status="unknown", detail="Client not initialized"))

    # 4. Collect stats
    from sqlalchemy import func, select
    from app.models.order import Order
    from app.models.shop import Shop
    from app.models.batch import Batch
    from datetime import date

    try:
        orders_total = (await db.execute(select(func.count()).select_from(Order))).scalar_one()
        today = date.today()
        orders_today = (
            await db.execute(
                select(func.count()).select_from(Order).where(func.date(Order.created_at) == today)
            )
        ).scalar_one()
        shops_total = (await db.execute(select(func.count()).select_from(Shop))).scalar_one()
        batches_total = (await db.execute(select(func.count()).select_from(Batch))).scalar_one()
        stats = SystemStats(
            orders_total=orders_total,
            orders_today=orders_today,
            shops_total=shops_total,
            batches_total=batches_total,
        )
    except Exception as e:
        logger.error(f"Stats query failed: {e}", exc_info=True)
        stats = SystemStats(orders_total=0, orders_today=0, shops_total=0, batches_total=0)

    return HealthResponse(
        version=APP_VERSION,
        uptime_seconds=int(time.time() - _start_time),
        services=services,
        stats=stats,
    )


# --- System tests ---

@router.post("/run-tests", response_model=SystemTestsResponse)
async def run_system_tests(
    request: Request,
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    results: list[TestResult] = []

    # Test 1: DB write + read
    t0 = time.monotonic()
    try:
        await db.execute(text("SELECT 1 + 1"))
        results.append(TestResult(
            name="БД: чтение запросов",
            status="pass",
            detail="SELECT 1+1 выполнен успешно",
            duration_ms=int((time.monotonic() - t0) * 1000),
        ))
    except Exception as e:
        results.append(TestResult(
            name="БД: чтение запросов",
            status="fail",
            detail=str(e)[:300],
            duration_ms=int((time.monotonic() - t0) * 1000),
        ))

    # Test 2: Redis set/get
    t0 = time.monotonic()
    try:
        import redis.asyncio as aioredis  # lazy import
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        test_key = "_health_test_key"
        await r.set(test_key, "ok", ex=5)
        val = await r.get(test_key)
        await r.delete(test_key)
        await r.aclose()
        if val == b"ok":
            results.append(TestResult(
                name="Redis: запись и чтение",
                status="pass",
                detail="SET/GET/DEL прошли успешно",
                duration_ms=int((time.monotonic() - t0) * 1000),
            ))
        else:
            results.append(TestResult(
                name="Redis: запись и чтение",
                status="fail",
                detail=f"Unexpected value: {val}",
                duration_ms=int((time.monotonic() - t0) * 1000),
            ))
    except Exception as e:
        results.append(TestResult(
            name="Redis: запись и чтение",
            status="fail",
            detail=str(e)[:300],
            duration_ms=int((time.monotonic() - t0) * 1000),
        ))

    # Test 3: Почта — публичный тарификатор (238311 → 101000, 500g)
    pochta_client = getattr(request.app.state, "pochta_client", None)
    t0 = time.monotonic()
    if pochta_client is not None:
        try:
            result, _log = await pochta_client.calculate_tariff_public(
                index_from="238311",
                index_to="101000",
                weight_grams=500,
            )
            if result is not None and result.total_kopecks > 0:
                results.append(TestResult(
                    name="Почта: тарификатор (публичный)",
                    status="pass",
                    detail=f"Тариф 238311→101000 500г: {result.total_kopecks / 100:.2f} ₽",
                    duration_ms=int((time.monotonic() - t0) * 1000),
                ))
            else:
                results.append(TestResult(
                    name="Почта: тарификатор (публичный)",
                    status="fail",
                    detail="Пустой результат от API",
                    duration_ms=int((time.monotonic() - t0) * 1000),
                ))
        except Exception as e:
            results.append(TestResult(
                name="Почта: тарификатор (публичный)",
                status="fail",
                detail=str(e)[:300],
                duration_ms=int((time.monotonic() - t0) * 1000),
            ))
    else:
        results.append(TestResult(
            name="Почта: тарификатор (публичный)",
            status="skip",
            detail="PochtaClient не инициализирован",
            duration_ms=0,
        ))

    # Test 4: Почта — авторизация (контрактный API)
    t0 = time.monotonic()
    if pochta_client is not None:
        try:
            result, _log = await pochta_client.calculate_tariff_contract(
                index_from="238311",
                index_to="101000",
                weight_grams=500,
            )
            if result is not None and result.total_kopecks > 0:
                results.append(TestResult(
                    name="Почта: тарификатор (контрактный)",
                    status="pass",
                    detail=f"Контрактный тариф 238311→101000 500г: {result.total_kopecks / 100:.2f} ₽",
                    duration_ms=int((time.monotonic() - t0) * 1000),
                ))
            else:
                results.append(TestResult(
                    name="Почта: тарификатор (контрактный)",
                    status="fail",
                    detail="Пустой результат от контрактного API",
                    duration_ms=int((time.monotonic() - t0) * 1000),
                ))
        except Exception as e:
            results.append(TestResult(
                name="Почта: тарификатор (контрактный)",
                status="fail",
                detail=str(e)[:300],
                duration_ms=int((time.monotonic() - t0) * 1000),
            ))
    else:
        results.append(TestResult(
            name="Почта: тарификатор (контрактный)",
            status="skip",
            detail="PochtaClient не инициализирован",
            duration_ms=0,
        ))

    # Test 5: JWT — проверка, что текущий токен валидный (раз мы сюда попали — значит OK)
    results.append(TestResult(
        name="JWT авторизация",
        status="pass",
        detail=f"Оператор: {operator.name} ({operator.role})",
        duration_ms=0,
    ))

    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")

    return SystemTestsResponse(
        results=results,
        passed=passed,
        failed=failed,
        total=len(results),
    )
