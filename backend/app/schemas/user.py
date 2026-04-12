from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class UserRegisterResponse(BaseModel):
    id: int
    name: str
    email: str
    token: str


class UserLoginRequest(BaseModel):
    identifier: str
    password: str


class UserProfileResponse(BaseModel):
    userId: int
    name: str
    image: Optional[str] = None
    day_learning_streak: int
    ranked_victories: int
    xpCurrent: int
    xpToNextLevel: int
    level: int


class UserAvatarResponse(BaseModel):
    result: bool
    image: Optional[str] = None


class UserLogoutRequest(BaseModel):
    token: Optional[str] = None


class UserLogoutResponse(BaseModel):
    success: bool


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    senha: Optional[str] = None


class UserUpdateResponse(BaseModel):
    id: int
    name: str
    email: str
    xp: int
    level: int
    total_score: int
    ranked_wins: int
    created_at: Optional[datetime] = None
