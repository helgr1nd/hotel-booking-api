from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.amenity import Amenity
from app.schemas.amenity import AmenityCreate, AmenityUpdate


class AmenityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Amenity]:
        result = await self.session.execute(select(Amenity))
        return list(result.scalars().all())

    async def get_by_id(self, amenity_id: int) -> Amenity | None:
        result = await self.session.execute(select(Amenity).where(Amenity.id == amenity_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Amenity | None:
        result = await self.session.execute(select(Amenity).where(Amenity.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, amenity_data: AmenityCreate) -> Amenity:
        amenity = Amenity(**amenity_data.model_dump())
        self.session.add(amenity)
        await self.session.commit()
        await self.session.refresh(amenity)
        return amenity

    async def update(self, amenity: Amenity, amenity_data: AmenityUpdate) -> Amenity:
        for field, value in amenity_data.model_dump(exclude_unset=True).items():
            setattr(amenity, field, value)
        await self.session.commit()
        await self.session.refresh(amenity)
        return amenity

    async def delete(self, amenity: Amenity) -> None:
        await self.session.delete(amenity)
        await self.session.commit()
