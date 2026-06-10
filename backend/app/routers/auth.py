from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserOut,
)
from app.schemas.common import APIResponse
from app.services.auth_service import generate_slug_from_name

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=APIResponse[AuthResponse], status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
        role="business_owner",
    )
    db.add(user)
    await db.flush()  # get user.id before commit

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(str(user.id), expires_delta)
    expires_at = datetime.now(timezone.utc) + expires_delta

    return APIResponse.ok(
        AuthResponse(
            user=UserOut.model_validate(user),
            access_token=token,
            expires_at=expires_at,
        )
    )


@router.post("/login", response_model=APIResponse[AuthResponse])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last_login_at
    user.last_login_at = datetime.now(timezone.utc)

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(str(user.id), expires_delta)
    expires_at = datetime.now(timezone.utc) + expires_delta

    return APIResponse.ok(
        AuthResponse(
            user=UserOut.model_validate(user),
            access_token=token,
            expires_at=expires_at,
        )
    )


@router.post("/logout", response_model=APIResponse[dict])
async def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWT — just acknowledge. Add token blocklist here if needed.
    return APIResponse.ok({"message": "Logged out successfully"})


@router.post("/forgot-password", response_model=APIResponse[dict])
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Always return success to prevent email enumeration
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user:
        # TODO: send reset email via Resend
        pass
    return APIResponse.ok({"message": "If this email exists, a reset link was sent"})


@router.post("/reset-password", response_model=APIResponse[dict])
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    # TODO: validate reset token from email, update password
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/me", response_model=APIResponse[UserOut])
async def get_me(current_user: User = Depends(get_current_user)):
    return APIResponse.ok(UserOut.model_validate(current_user))


@router.patch("/me", response_model=APIResponse[UserOut])
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.phone is not None:
        current_user.phone = body.phone
    return APIResponse.ok(UserOut.model_validate(current_user))
