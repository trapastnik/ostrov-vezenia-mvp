import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import hash_password
from app.models.operator import Operator


async def main():
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip()
    password = input("Admin password: ").strip()

    if not all([name, email, password]):
        print("All fields are required")
        sys.exit(1)

    async with async_session() as db:
        existing = await db.execute(select(Operator).where(Operator.email == email))
        if existing.scalar_one_or_none():
            print(f"Operator with email {email} already exists")
            sys.exit(1)

        operator = Operator(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
        )
        db.add(operator)
        await db.commit()
        print(f"Admin '{name}' created successfully")


if __name__ == "__main__":
    asyncio.run(main())
