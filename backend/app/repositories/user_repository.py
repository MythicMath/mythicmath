from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        name: str,
        photo_url: Optional[str] = None,
    ) -> User:
        user = User(name=name, photo_url=photo_url)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
