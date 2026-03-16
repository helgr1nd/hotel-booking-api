from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.room import Room
from app.models.amenity import Amenity
from app.models.booking import Booking, BookingStatus
from app.schemas.room import RoomCreate, RoomUpdate


class RoomRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, is_active: bool = True) -> list[Room]:
        query = select(Room).options(selectinload(Room.amenities))
        if is_active:
            query = query.where(Room.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, room_id: int) -> Room | None:
        result = await self.session.execute(
            select(Room).options(selectinload(Room.amenities)).where(Room.id == room_id)
        )
        return result.scalar_one_or_none()

    async def create(self, room_data: RoomCreate) -> Room:
        amenity_ids = room_data.amenity_ids
        room_dict = room_data.model_dump(exclude={"amenity_ids"})
        room = Room(**room_dict)
        
        if amenity_ids:
            amenities = await self.session.execute(
                select(Amenity).where(Amenity.id.in_(amenity_ids))
            )
            room.amenities = list(amenities.scalars().all())
        
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room, ["amenities"])
        return room

    async def update(self, room: Room, room_data: RoomUpdate) -> Room:
        update_dict = room_data.model_dump(exclude_unset=True, exclude={"amenity_ids"})
        for field, value in update_dict.items():
            setattr(room, field, value)
        
        if room_data.amenity_ids is not None:
            amenities = await self.session.execute(
                select(Amenity).where(Amenity.id.in_(room_data.amenity_ids))
            )
            room.amenities = list(amenities.scalars().all())
        
        await self.session.commit()
        await self.session.refresh(room, ["amenities"])
        return room

    async def get_available_rooms(
        self,
        start_at: datetime,
        end_at: datetime,
        capacity_min: int | None = None,
        amenity_ids: list[int] | None = None,
        floor: int | None = None,
    ) -> list[Room]:
        query = select(Room).options(selectinload(Room.amenities)).where(Room.is_active == True)
        
        if capacity_min:
            query = query.where(Room.capacity >= capacity_min)
        
        if floor is not None:
            query = query.where(Room.floor == floor)
        
        if amenity_ids:
            for amenity_id in amenity_ids:
                query = query.where(Room.amenities.any(Amenity.id == amenity_id))
        
        result = await self.session.execute(query)
        all_rooms = list(result.scalars().all())
        
        available_rooms = []
        for room in all_rooms:
            has_conflict = await self._has_booking_conflict(room.id, start_at, end_at)
            if not has_conflict:
                available_rooms.append(room)
        
        return available_rooms

    async def _has_booking_conflict(
        self, room_id: int, start_at: datetime, end_at: datetime
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
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
