from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_operator, get_db
from app.models.grouping_settings import GroupingSettings
from app.models.operator import Operator
from app.models.order import Order
from app.models.shipment_group import ShipmentGroup
from app.models.tracking_event import TrackingEvent

router = APIRouter(prefix="/admin", tags=["admin-groups"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ShipmentGroupOut(BaseModel):
    id: str
    number: str
    hub: str
    hub_name: str
    transport_type: str
    status: str
    orders_count: int
    total_weight_grams: int
    public_cost_kopecks: int
    contract_cost_kopecks: int
    savings_kopecks: int
    savings_percent: float
    scheduled_at: str | None
    dispatched_at: str | None
    arrived_at_hub_at: str | None
    operator_note: str | None
    created_at: str


class ShipmentGroupsResponse(BaseModel):
    items: list[ShipmentGroupOut]
    total: int
    page: int
    page_size: int


class GroupStatusUpdate(BaseModel):
    status: str
    operator_note: str | None = None


class ForceDispatchRequest(BaseModel):
    note: str | None = None


class GroupingSettingsOut(BaseModel):
    id: str
    scope: str
    scope_name: str
    enabled: bool
    max_wait_hours: int
    min_group_size: int
    min_savings_rub: int
    penalty_per_hour_rub: float
    worker_interval_minutes: int
    description: str | None


class GroupingSettingsUpdate(BaseModel):
    enabled: bool | None = None
    max_wait_hours: int | None = None
    min_group_size: int | None = None
    min_savings_rub: int | None = None
    penalty_per_hour_rub: float | None = None
    worker_interval_minutes: int | None = None
    description: str | None = None


# ── Groups endpoints ──────────────────────────────────────────────────────────

@router.get("/groups", response_model=ShipmentGroupsResponse)
async def list_groups(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    hub: str | None = None,
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    q = select(ShipmentGroup)
    if status:
        q = q.where(ShipmentGroup.status == status)
    if hub:
        q = q.where(ShipmentGroup.hub == hub)
    q = q.order_by(ShipmentGroup.created_at.desc())

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    groups = list(result.scalars().all())

    return ShipmentGroupsResponse(
        items=[_group_to_out(g) for g in groups],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/groups/{group_id}", response_model=ShipmentGroupOut)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    result = await db.execute(select(ShipmentGroup).where(ShipmentGroup.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена")
    return _group_to_out(group)


@router.patch("/groups/{group_id}/status")
async def update_group_status(
    group_id: str,
    body: GroupStatusUpdate,
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    result = await db.execute(select(ShipmentGroup).where(ShipmentGroup.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена")

    allowed_transitions = {
        "forming": ["ready", "cancelled"],
        "ready": ["dispatched", "cancelled"],
        "dispatched": ["at_hub"],
        "at_hub": ["completed"],
    }
    if body.status not in allowed_transitions.get(group.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Переход {group.status} → {body.status} недопустим",
        )

    from datetime import datetime, timezone
    group.status = body.status
    if body.operator_note:
        group.operator_note = body.operator_note
    if body.status == "dispatched":
        group.dispatched_at = datetime.now(timezone.utc)
    elif body.status == "at_hub":
        group.arrived_at_hub_at = datetime.now(timezone.utc)

    # Добавляем tracking event для всех заказов группы
    orders_result = await db.execute(select(Order).where(Order.shipment_group_id == group_id))
    orders = list(orders_result.scalars().all())

    event_map = {
        "dispatched": ("group_dispatched", "Группа отправлена", "Калининград"),
        "at_hub": ("group_at_hub", f"Группа прибыла в хаб {group.hub_name}", group.hub_name),
        "cancelled": ("cancelled", "Группа отменена", None),
    }
    if body.status in event_map:
        etype, edesc, eloc = event_map[body.status]
        for order in orders:
            event = TrackingEvent(
                order_id=order.id,
                shipment_group_id=group.id,
                internal_track_number=order.internal_track_number,
                event_type=etype,
                description=edesc,
                location=eloc,
            )
            db.add(event)

    await db.commit()
    return {"ok": True, "status": group.status}


@router.post("/groups/{group_id}/force-dispatch")
async def force_dispatch_group(
    group_id: str,
    body: ForceDispatchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    """Принудительно отправить группу, игнорируя оптимизатор."""
    result = await db.execute(select(ShipmentGroup).where(ShipmentGroup.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена")
    if group.status not in ("forming", "ready"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Группа в статусе {group.status}, принудительная отправка невозможна",
        )

    from datetime import datetime, timezone
    group.status = "dispatched"
    group.dispatched_at = datetime.now(timezone.utc)
    group.operator_note = body.note or "Принудительная отправка оператором"

    orders_result = await db.execute(select(Order).where(Order.shipment_group_id == group_id))
    orders = list(orders_result.scalars().all())
    for order in orders:
        event = TrackingEvent(
            order_id=order.id,
            shipment_group_id=group.id,
            internal_track_number=order.internal_track_number,
            event_type="group_dispatched",
            description="Группа отправлена (принудительно)",
            location="Калининград",
        )
        db.add(event)

    await db.commit()
    return {"ok": True, "group_number": group.number, "orders_count": len(orders)}


# ── Settings endpoints ────────────────────────────────────────────────────────

@router.get("/groups/settings/global", response_model=GroupingSettingsOut)
async def get_grouping_settings(
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    result = await db.execute(
        select(GroupingSettings).where(GroupingSettings.scope == "global")
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = GroupingSettings(scope="global", scope_name="Глобальные настройки")
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return _settings_to_out(settings)


@router.patch("/groups/settings/global", response_model=GroupingSettingsOut)
async def update_grouping_settings(
    body: GroupingSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    operator: Operator = Depends(get_current_operator),
):
    result = await db.execute(
        select(GroupingSettings).where(GroupingSettings.scope == "global")
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = GroupingSettings(scope="global", scope_name="Глобальные настройки")
        db.add(settings)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return _settings_to_out(settings)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _group_to_out(g: ShipmentGroup) -> ShipmentGroupOut:
    return ShipmentGroupOut(
        id=str(g.id),
        number=g.number,
        hub=g.hub,
        hub_name=g.hub_name,
        transport_type=g.transport_type,
        status=g.status,
        orders_count=g.orders_count,
        total_weight_grams=g.total_weight_grams,
        public_cost_kopecks=g.public_cost_kopecks,
        contract_cost_kopecks=g.contract_cost_kopecks,
        savings_kopecks=g.savings_kopecks,
        savings_percent=g.savings_percent,
        scheduled_at=g.scheduled_at.isoformat() if g.scheduled_at else None,
        dispatched_at=g.dispatched_at.isoformat() if g.dispatched_at else None,
        arrived_at_hub_at=g.arrived_at_hub_at.isoformat() if g.arrived_at_hub_at else None,
        operator_note=g.operator_note,
        created_at=g.created_at.isoformat(),
    )


def _settings_to_out(s: GroupingSettings) -> GroupingSettingsOut:
    return GroupingSettingsOut(
        id=str(s.id),
        scope=s.scope,
        scope_name=s.scope_name,
        enabled=s.enabled,
        max_wait_hours=s.max_wait_hours,
        min_group_size=s.min_group_size,
        min_savings_rub=s.min_savings_rub,
        penalty_per_hour_rub=s.penalty_per_hour_rub,
        worker_interval_minutes=s.worker_interval_minutes,
        description=s.description,
    )
