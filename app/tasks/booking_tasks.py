import asyncio
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.db.session import async_session
from app.models.booking import Booking, BookingStatus
from app.core.cache import delete_cache_pattern
from sqlalchemy import select


@celery_app.task
def expire_pending_booking(booking_id: int):
    asyncio.run(_expire_pending_booking(booking_id))


async def _expire_pending_booking(booking_id: int):
    async with async_session() as session:
        result = await session.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()
        
        if booking and booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.EXPIRED
            booking.updated_at = datetime.utcnow()
            await session.commit()
            
            await delete_cache_pattern("availability:*")
            await delete_cache_pattern(f"booking:{booking_id}")
            
            print(f"Booking {booking_id} expired")


@celery_app.task
def send_booking_reminder(booking_id: int):
    asyncio.run(_send_booking_reminder(booking_id))


async def _send_booking_reminder(booking_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if booking and booking.status == BookingStatus.CONFIRMED:
            print(f"Reminder: Booking {booking_id} starts at {booking.start_at}")
            print(f"Room: {booking.room_id}, User: {booking.user_id}")
