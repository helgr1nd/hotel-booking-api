import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


async def create_user_and_login(client: AsyncClient, username: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "password123",
        },
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    return response.json()["access_token"]


async def create_room(client: AsyncClient, token: str) -> int:
    response = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Test Room",
            "floor": 1,
            "capacity": 5,
            "amenity_ids": [],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient):
    admin_token = await create_user_and_login(client, "admin")
    room_id = await create_room(client, admin_token)
    
    user_token = await create_user_and_login(client, "user1")
    
    start_at = datetime.utcnow() + timedelta(hours=1)
    end_at = start_at + timedelta(hours=1)
    
    response = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "purpose": "Team meeting",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["room_id"] == room_id
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_create_booking_in_past(client: AsyncClient):
    admin_token = await create_user_and_login(client, "admin")
    room_id = await create_room(client, admin_token)
    
    user_token = await create_user_and_login(client, "user1")
    
    start_at = datetime.utcnow() - timedelta(hours=1)
    end_at = start_at + timedelta(hours=1)
    
    response = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert "past" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_booking_conflict(client: AsyncClient):
    admin_token = await create_user_and_login(client, "admin")
    room_id = await create_room(client, admin_token)
    
    user1_token = await create_user_and_login(client, "user1")
    user2_token = await create_user_and_login(client, "user2")
    
    start_at = datetime.utcnow() + timedelta(hours=1)
    end_at = start_at + timedelta(hours=1)
    
    response1 = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
        headers={"Authorization": f"Bearer {user1_token}"},
    )
    assert response1.status_code == 201
    
    response2 = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
        headers={"Authorization": f"Bearer {user2_token}"},
    )
    assert response2.status_code == 409
