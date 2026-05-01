import secrets
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.services.security import hash_password, verify_password


class UserService:
    def __init__(self, repository: Optional[UserRepository] = None) -> None:
        self.repository = repository or UserRepository()

    async def get_user(self, session: AsyncSession, user_id: int):
        return await self.repository.get_by_id(session, user_id)

    async def get_user_by_email(self, session: AsyncSession, email: str):
        return await self.repository.get_by_email(session, email)

    async def get_user_by_username(self, session: AsyncSession, username: str):
        return await self.repository.get_by_username(session, username)

    async def get_user_by_google_sub(self, session: AsyncSession, google_sub: str):
        return await self.repository.get_by_google_sub(session, google_sub)

    async def create_user(
        self,
        session: AsyncSession,
        username: str,
        email: str,
        password: str,
        photo_url: Optional[str] = None,
    ):
        password_hash = hash_password(password)
        return await self.repository.create(
            session,
            username=username,
            email=email,
            password_hash=password_hash,
            photo_url=photo_url,
        )

    async def create_google_user(
        self,
        session: AsyncSession,
        username: str,
        email: str,
        google_sub: str,
        photo_url: Optional[str] = None,
    ):
        password_hash = hash_password(secrets.token_urlsafe(32))
        return await self.repository.create(
            session,
            username=username,
            email=email,
            password_hash=password_hash,
            photo_url=photo_url,
            google_sub=google_sub,
        )

    async def link_google_identity(
        self,
        session: AsyncSession,
        user,
        google_sub: str,
        photo_url: Optional[str] = None,
    ):
        return await self.repository.update(
            session,
            user=user,
            google_sub=google_sub,
            photo_url=photo_url if not user.photo_url else None,
        )

    async def update_user(
        self,
        session: AsyncSession,
        user,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ):
        password_hash = None
        if password is not None:
            password_hash = hash_password(password)
        return await self.repository.update(
            session,
            user=user,
            email=email,
            password_hash=password_hash,
        )

    def verify_password(self, password: str, password_hash: str) -> bool:
        return verify_password(password, password_hash)
