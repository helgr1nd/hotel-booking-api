from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.amenity import AmenityCreate, AmenityUpdate, AmenityResponse
from app.repositories.amenity_repository import AmenityRepository
from app.api.dependencies import get_current_admin
from app.models.user import User
from app.core.cache import delete_cache_pattern

router = APIRouter()


@router.get("", response_model=list[AmenityResponse])
async def get_amenities(session: AsyncSession = Depends(get_db)):
    amenity_repo = AmenityRepository(session)
    amenities = await amenity_repo.get_all()
    return amenities


@router.post("", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(
    amenity_data: AmenityCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    amenity_repo = AmenityRepository(session)
    
    existing = await amenity_repo.get_by_slug(amenity_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amenity with this slug already exists",
        )
    
    amenity = await amenity_repo.create(amenity_data)
    await delete_cache_pattern("rooms:*")
    await delete_cache_pattern("availability:*")
    return amenity


@router.patch("/{amenity_id}", response_model=AmenityResponse)
async def update_amenity(
    amenity_id: int,
    amenity_data: AmenityUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    amenity_repo = AmenityRepository(session)
    amenity = await amenity_repo.get_by_id(amenity_id)
    
    if not amenity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Amenity not found",
        )
    
    if amenity_data.slug and amenity_data.slug != amenity.slug:
        existing = await amenity_repo.get_by_slug(amenity_data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amenity with this slug already exists",
            )
    
    amenity = await amenity_repo.update(amenity, amenity_data)
    await delete_cache_pattern("rooms:*")
    await delete_cache_pattern("availability:*")
    return amenity


@router.delete("/{amenity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_amenity(
    amenity_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    amenity_repo = AmenityRepository(session)
    amenity = await amenity_repo.get_by_id(amenity_id)
    
    if not amenity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Amenity not found",
        )
    
    await amenity_repo.delete(amenity)
    await delete_cache_pattern("rooms:*")
    await delete_cache_pattern("availability:*")
