from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreate


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, booking_id: int) -> Booking | None:
        result = await self.session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking).where(Booking.user_id == user_id).order_by(Booking.start_at.desc())
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Booking]:
        result = await self.session.execute(select(Booking).order_by(Booking.start_at.desc()))
        return list(result.scalars().all())

    async def create(self, user_id: int, booking_data: BookingCreate) -> Booking:
        booking = Booking(
            user_id=user_id,
            room_id=booking_data.room_id,
            start_at=booking_data.start_at,
            end_at=booking_data.end_at,
            purpose=booking_data.purpose,
            status=BookingStatus.PENDING,
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def update_status(self, booking: Booking, status: BookingStatus) -> Booking:
        booking.status = status
        booking.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def has_conflict(
        self, room_id: int, start_at: datetime, end_at: datetime, exclude_booking_id: int | None = None
    ) -> bool:
        query = select(Booking).where(
            and_(
                Booking.room_id == room_id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                or_(
                    and_(Booking.start_at < end_at, Booking.end_at > start_at),
                ),
            )
        )
        
        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
