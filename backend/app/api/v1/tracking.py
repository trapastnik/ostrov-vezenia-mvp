from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.core.database import async_session
from app.models.order import Order
from app.models.tracking_event import TrackingEvent
from app.models.shipment_group import ShipmentGroup

router = APIRouter(prefix="/track", tags=["tracking"])


class TrackingEventOut(BaseModel):
    event_type: str
    description: str
    location: str | None
    details: str | None
    created_at: str


class TrackingResponse(BaseModel):
    order_id: str
    external_order_id: str
    internal_track_number: str | None
    track_number: str | None
    status: str
    recipient_name: str
    recipient_postal_code: str
    shipment_group_number: str | None
    hub_name: str | None
    events: list[TrackingEventOut]


async def _build_tracking_response(order: Order, session) -> TrackingResponse:
    """Собирает TrackingResponse для заказа."""
    # Загружаем TrackingEvent по order_id (а не только по track_number)
    events_result = await session.execute(
        select(TrackingEvent)
        .where(TrackingEvent.order_id == order.id)
        .order_by(TrackingEvent.created_at)
    )
    events = list(events_result.scalars().all())

    group = None
    if order.shipment_group_id:
        group_result = await session.execute(
            select(ShipmentGroup).where(ShipmentGroup.id == order.shipment_group_id)
        )
        group = group_result.scalar_one_or_none()

    return TrackingResponse(
        order_id=str(order.id),
        external_order_id=order.external_order_id,
        internal_track_number=order.internal_track_number,
        track_number=order.track_number,
        status=order.status,
        recipient_name=order.recipient_name,
        recipient_postal_code=order.recipient_postal_code,
        shipment_group_number=group.number if group else None,
        hub_name=group.hub_name if group else None,
        events=[
            TrackingEventOut(
                event_type=e.event_type,
                description=e.description,
                location=e.location,
                details=e.details,
                created_at=e.created_at.isoformat(),
            )
            for e in events
        ],
    )


@router.get("/search/{query}", response_model=TrackingResponse)
async def search_tracking(query: str):
    """Поиск по номеру заказа магазина, трек-номеру ПР или внутреннему трек-номеру."""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(
                or_(
                    Order.external_order_id == query,
                    Order.track_number == query,
                    Order.internal_track_number == query,
                )
            )
        )
        order = result.scalar_one_or_none()

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заказ «{query}» не найден",
            )

        return await _build_tracking_response(order, session)


@router.get("/{track_number}", response_model=TrackingResponse)
async def get_tracking(track_number: str):
    """Трекинг по внутреннему трек-номеру (OV-YYYYMMDD-XXXXX)."""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.internal_track_number == track_number)
        )
        order = result.scalar_one_or_none()

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек-номер {track_number} не найден",
            )

        return await _build_tracking_response(order, session)
