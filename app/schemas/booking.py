from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.booking import BookingStatus


class BookingBase(BaseModel):
    room_id: int
    start_at: datetime
    end_at: datetime
    purpose: str | None = Field(None, max_length=500)

    @field_validator("end_at")
    @classmethod
    def validate_end_after_start(cls, v, info):
        if "start_at" in info.data and v <= info.data["start_at"]:
            raise ValueError("end_at must be after start_at")
        return v


class BookingCreate(BookingBase):
    pass


class BookingResponse(BookingBase):
    id: int
    user_id: int
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    bookings: list[BookingResponse]
    total: int
