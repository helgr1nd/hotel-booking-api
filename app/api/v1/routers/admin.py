from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.booking import BookingResponse
from app.repositories.booking_repository import BookingRepository
from app.api.dependencies import get_current_admin
from app.models.user import User

router = APIRouter()


@router.get("/bookings", response_model=list[BookingResponse])
async def get_all_bookings(
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    booking_repo = BookingRepository(session)
    bookings = await booking_repo.get_all()
    return bookings
