from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository: Optional[UserRepository] = None) -> None:
        self.repository = repository or UserRepository()

    async def get_user(self, session: AsyncSession, user_id: int):
        return await self.repository.get_by_id(session, user_id)

    async def create_user(
        self, session: AsyncSession, name: str, photo_url: Optional[str] = None
    ):
        return await self.repository.create(session, name=name, photo_url=photo_url)
