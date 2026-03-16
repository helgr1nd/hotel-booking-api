from pydantic import BaseModel, Field


class AmenityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)


class AmenityCreate(AmenityBase):
    pass


class AmenityUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(None, min_length=1, max_length=100)


class AmenityResponse(AmenityBase):
    id: int

    class Config:
        from_attributes = True
