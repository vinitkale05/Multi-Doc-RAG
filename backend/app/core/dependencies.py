from typing import Optional
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.models import User, Tenant

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not auth or not auth.credentials:
        raise AuthenticationError("Missing Bearer Authorization Token")

    try:
        payload = decode_token(auth.credentials)
    except ValueError as e:
        raise AuthenticationError(str(e))

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing user subject")

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise AuthenticationError("User not found or deactivated")

    return user


def require_role(allowed_roles: list[str]):
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise PermissionDeniedError(f"User role '{user.role}' not authorized. Required: {allowed_roles}")
        return user
    return role_checker


require_admin = require_role(["admin"])
require_member = require_role(["admin", "member"])
require_viewer = require_role(["admin", "member", "viewer"])
