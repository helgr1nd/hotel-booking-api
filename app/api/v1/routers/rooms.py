from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.session import get_db
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse
from app.repositories.room_repository import RoomRepository
from app.api.dependencies import get_current_admin
from app.models.user import User
from app.core.cache import get_cache, set_cache, delete_cache_pattern

router = APIRouter()


@router.get("", response_model=list[RoomResponse])
async def get_rooms(session: AsyncSession = Depends(get_db)):
    cache_key = "rooms:all"
    cached = await get_cache(cache_key)
    if cached:
        return cached
    
    room_repo = RoomRepository(session)
    rooms = await room_repo.get_all()
    
    result = [RoomResponse.model_validate(room) for room in rooms]
    await set_cache(cache_key, [r.model_dump(mode="json") for r in result], ttl=300)
    
    return result


@router.get("/availability", response_model=list[RoomResponse])
async def get_available_rooms(
    start_at: datetime = Query(...),
    end_at: datetime = Query(...),
    capacity_min: int | None = Query(None, gt=0),
    amenity_ids: list[int] | None = Query(None),
    floor: int | None = Query(None),
    session: AsyncSession = Depends(get_db),
):
    if end_at <= start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_at must be after start_at",
        )
    
    cache_key = f"availability:{start_at.isoformat()}:{end_at.isoformat()}:{capacity_min}:{amenity_ids}:{floor}"
    cached = await get_cache(cache_key)
    if cached:
        return cached
    
    room_repo = RoomRepository(session)
    rooms = await room_repo.get_available_rooms(
        start_at=start_at,
        end_at=end_at,
        capacity_min=capacity_min,
        amenity_ids=amenity_ids,
        floor=floor,
    )
    
    result = [RoomResponse.model_validate(room) for room in rooms]
    await set_cache(cache_key, [r.model_dump(mode="json") for r in result], ttl=60)
    
    return result


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: int, session: AsyncSession = Depends(get_db)):
    room_repo = RoomRepository(session)
    room = await room_repo.get_by_id(room_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    
    return room


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    room_repo = RoomRepository(session)
    room = await room_repo.create(room_data)
    
    await delete_cache_pattern("rooms:*")
    await delete_cache_pattern("availability:*")
    
    return room


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    room_data: RoomUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    room_repo = RoomRepository(session)
    room = await room_repo.get_by_id(room_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    
    room = await room_repo.update(room, room_data)
    
    await delete_cache_pattern("rooms:*")
    await delete_cache_pattern("availability:*")
    
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    room_repo = RoomRepository(session)
    room = await room_repo.get_by_id(room_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    
    room.is_active = False
    await session.commit()
    
    await delete_cache_pattern("rooms:*")
    await delete_cache_pattern("availability:*")
