from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/track", tags=["tracking"])


class TrackingEventOut(BaseModel):
    event_type: str
    description: str
    location: str | None
    details: str | None
    created_at: str


class TrackingResponse(BaseModel):
    internal_track_number: str
    status: str
    recipient_name: str
    recipient_postal_code: str
    shipment_group_number: str | None
    hub_name: str | None
    events: list[TrackingEventOut]


@router.get("/{track_number}", response_model=TrackingResponse)
async def get_tracking(track_number: str, request: Request):
    from sqlalchemy import select
    from app.core.database import async_session
    from app.models.order import Order
    from app.models.tracking_event import TrackingEvent
    from app.models.shipment_group import ShipmentGroup

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

        events_result = await session.execute(
            select(TrackingEvent)
            .where(TrackingEvent.internal_track_number == track_number)
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
        internal_track_number=track_number,
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
