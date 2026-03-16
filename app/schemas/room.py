from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.amenity import AmenityResponse


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    floor: int
    capacity: int = Field(..., gt=0)


class RoomCreate(RoomBase):
    amenity_ids: list[int] = []


class RoomUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    floor: int | None = None
    capacity: int | None = Field(None, gt=0)
    is_active: bool | None = None
    amenity_ids: list[int] | None = None


class RoomResponse(RoomBase):
    id: int
    is_active: bool
    created_at: datetime
    amenities: list[AmenityResponse] = []

    class Config:
        from_attributes = True


class RoomAvailabilityQuery(BaseModel):
    start_at: datetime
    end_at: datetime
    capacity_min: int | None = Field(None, gt=0)
    amenity_ids: list[int] | None = None
    floor: int | None = None
