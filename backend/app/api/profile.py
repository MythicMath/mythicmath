from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.database import get_session as get_db_session
from app.schemas.user import UserProfileResponse
from app.services.session_service import get_session as get_auth_session
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db_session),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
        )

    token = authorization.split(" ", 1)[1].strip()
    session_data = await get_auth_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = session_data.get("user_id")
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def calculate_xp_to_next_level(level: int) -> int:
    return (level + 1) * 100


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user=Depends(get_current_user)):
    xp_to_next_level = calculate_xp_to_next_level(current_user.level)

    return UserProfileResponse(
        userId=current_user.id,
        name=current_user.name,
        image=current_user.photo_url,
        day_learning_streak=0,
        ranked_victories=current_user.ranked_wins,
        xpCurrent=current_user.xp,
        xpToNextLevel=xp_to_next_level,
        level=current_user.level,
    )
