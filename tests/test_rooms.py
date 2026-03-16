import pytest
from httpx import AsyncClient


async def get_admin_token(client: AsyncClient) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "username": "admin",
            "password": "admin123",
        },
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_get_rooms_empty(client: AsyncClient):
    response = await client.get("/api/v1/rooms")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_room_as_admin(client: AsyncClient):
    token = await get_admin_token(client)
    
    response = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Conference Room A",
            "floor": 1,
            "capacity": 10,
            "amenity_ids": [],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Conference Room A"
    assert data["floor"] == 1
    assert data["capacity"] == 10


@pytest.mark.asyncio
async def test_create_room_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Conference Room A",
            "floor": 1,
            "capacity": 10,
            "amenity_ids": [],
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_room_by_id(client: AsyncClient):
    token = await get_admin_token(client)
    
    create_response = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Conference Room A",
            "floor": 1,
            "capacity": 10,
            "amenity_ids": [],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    room_id = create_response.json()["id"]
    
    response = await client.get(f"/api/v1/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == "Conference Room A"
