from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.db.session import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.repositories.booking_repository import BookingRepository
from app.repositories.room_repository import RoomRepository
from app.api.dependencies import get_current_user, get_current_admin
from app.models.user import User
from app.models.booking import BookingStatus
from app.core.cache import delete_cache_pattern
from app.tasks.booking_tasks import expire_pending_booking, send_booking_reminder
from app.config import settings

router = APIRouter()


@router.get("", response_model=list[BookingResponse])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    booking_repo = BookingRepository(session)
    bookings = await booking_repo.get_by_user(current_user.id)
    return bookings





@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if booking_data.start_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create booking in the past",
        )
    
    duration = (booking_data.end_at - booking_data.start_at).total_seconds() / 60
    if duration < 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum booking duration is 15 minutes",
        )
    
    room_repo = RoomRepository(session)
    room = await room_repo.get_by_id(booking_data.room_id)
    
    if not room or not room.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found or inactive",
        )
    
    booking_repo = BookingRepository(session)
    has_conflict = await booking_repo.has_conflict(
        booking_data.room_id,
        booking_data.start_at,
        booking_data.end_at,
    )
    
    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is not available for the selected time",
        )
    
    booking = await booking_repo.create(current_user.id, booking_data)
    
    expire_pending_booking.apply_async(
        args=[booking.id],
        countdown=settings.PENDING_BOOKING_EXPIRE_MINUTES * 60,
    )
    
    await delete_cache_pattern("availability:*")
    
    return booking


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    booking_repo = BookingRepository(session)
    booking = await booking_repo.get_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return booking


@router.post("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    booking_repo = BookingRepository(session)
    booking = await booking_repo.get_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be confirmed",
        )
    
    has_conflict = await booking_repo.has_conflict(
        booking.room_id,
        booking.start_at,
        booking.end_at,
        exclude_booking_id=booking.id,
    )
    
    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is no longer available for the selected time",
        )
    
    booking = await booking_repo.update_status(booking, BookingStatus.CONFIRMED)
    
    reminder_time = booking.start_at - timedelta(minutes=settings.BOOKING_REMINDER_MINUTES)
    if reminder_time > datetime.utcnow():
        send_booking_reminder.apply_async(
            args=[booking.id],
            eta=reminder_time,
        )
    
    await delete_cache_pattern("availability:*")
    
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    booking_repo = BookingRepository(session)
    booking = await booking_repo.get_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.EXPIRED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled or expired",
        )
    
    booking = await booking_repo.update_status(booking, BookingStatus.CANCELLED)
    
    await delete_cache_pattern("availability:*")
    
    return booking
