import re
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.database import get_session
from app.schemas.user import (
    UserLoginRequest,
    UserLogoutRequest,
    UserLogoutResponse,
    UserGoogleLoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.services.google_auth import (
    GoogleAuthConfigError,
    GoogleAuthError,
    verify_google_id_token,
)
from app.services.user_service import UserService
from app.services.validation import is_valid_email
from app.services.session_service import create_session, revoke_session

router = APIRouter()
user_service = UserService()


def _clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_username_candidate(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("._-")
    return cleaned[:60] or "google_user"


async def _build_unique_google_username(
    session: AsyncSession,
    display_name: str,
) -> str:
    base = _clean_username_candidate(display_name)
    candidate = base
    suffix = 1

    while await user_service.get_user_by_username(session, candidate):
        suffix_text = f"_{suffix}"
        candidate = f"{base[:255 - len(suffix_text)]}{suffix_text}"
        suffix += 1

    return candidate


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    username = _clean_str(payload.username)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username is required",
        )

    email = _clean_str(payload.email)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email is required",
        )

    if not is_valid_email(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format",
        )

    email = email.lower()
    existing = await user_service.get_user_by_email(session, email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    existing_username = await user_service.get_user_by_username(session, username)
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

    user = await user_service.create_user(
        session=session,
        username=username,
        email=email,
        password=payload.password,
    )

    token = await create_session(user_id=user.id, email=user.email)

    return UserRegisterResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        token=token,
    )


@router.post("/login", response_model=UserRegisterResponse)
async def login_user(
    payload: UserLoginRequest,
    session: AsyncSession = Depends(get_session),
):
    identifier = _clean_str(payload.identifier)
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Identifier is required",
        )

    if "@" in identifier:
        user = await user_service.get_user_by_email(session, identifier.lower())
    else:
        user = await user_service.get_user_by_username(session, identifier)

    if not user or not user_service.verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = await create_session(user_id=user.id, email=user.email)
    return UserRegisterResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        token=token,
    )


@router.post("/login/google", response_model=UserRegisterResponse)
async def login_google_user(
    payload: UserGoogleLoginRequest,
    session: AsyncSession = Depends(get_session),
):
    google_token = _clean_str(payload.id_token) or _clean_str(payload.credential)
    if not google_token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Google ID token is required",
        )

    try:
        google_identity = await verify_google_id_token(google_token)
    except GoogleAuthConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except GoogleAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user = await user_service.get_user_by_google_sub(session, google_identity.subject)
    if not user:
        user = await user_service.get_user_by_email(session, google_identity.email)

    if user:
        if user.google_sub and user.google_sub != google_identity.subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already linked to another Google account",
            )
        if not user.google_sub:
            user = await user_service.link_google_identity(
                session=session,
                user=user,
                google_sub=google_identity.subject,
                photo_url=google_identity.picture,
            )
    else:
        username = await _build_unique_google_username(session, google_identity.name)
        user = await user_service.create_google_user(
            session=session,
            username=username,
            email=google_identity.email,
            google_sub=google_identity.subject,
            photo_url=google_identity.picture,
        )

    token = await create_session(user_id=user.id, email=user.email)
    return UserRegisterResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        token=token,
    )


@router.post("/logout", response_model=UserLogoutResponse)
async def logout_user(
    payload: Optional[UserLogoutRequest] = None,
    authorization: Optional[str] = Header(None),
):
    token: Optional[str] = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token and payload and payload.token:
        token = _clean_str(payload.token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )

    await revoke_session(token)
    return UserLogoutResponse(success=True)
