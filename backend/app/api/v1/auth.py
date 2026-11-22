from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.errors import AuthenticationError, AppError
from app.core.dependencies import get_current_user
from app.models import User, Tenant, AuditLog
from app.schemas import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse

router = APIRouter(tags=["Authentication"])


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalars().first():
        raise AppError(status_code=400, detail="User with this email already exists", code="EMAIL_EXISTS")

    # Create new tenant
    tenant = Tenant(name=req.tenant_name or "Workspace")
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role or "admin",
        tenant_id=tenant.id
    )
    db.add(user)
    await db.flush()

    # Audit log
    audit = AuditLog(actor_id=user.id, tenant_id=tenant.id, action="USER_REGISTERED", resource=user.id)
    db.add(audit)
    await db.commit()

    token_data = {"sub": user.id, "email": user.email, "role": user.role, "tenant_id": tenant.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()
    if not user or not verify_password(req.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    token_data = {"sub": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_tokens(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
    except ValueError as e:
        raise AuthenticationError(f"Invalid refresh token: {str(e)}")

    if payload.get("type") != "refresh":
        raise AuthenticationError("Token is not a refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise AuthenticationError("User not found")

    token_data = {"sub": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60
    )


@router.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        tenant_id=user.tenant_id,
        created_at=user.created_at
    )
