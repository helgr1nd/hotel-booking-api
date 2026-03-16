import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import async_session
from app.models.user import User
from app.core.security import get_password_hash


async def create_admin():
    async with async_session() as session:
        admin = User(
            email="admin@example.com",
            username="admin",
            password_hash=get_password_hash("admin123"),
            is_admin=True,
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print("Admin created successfully!")
        print("Email: admin@example.com")
        print("Username: admin")
        print("Password: admin123")


if __name__ == "__main__":
    asyncio.run(create_admin())
