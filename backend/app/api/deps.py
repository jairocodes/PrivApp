"""Dependencias de FastAPI reutilizables."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TokenInvalidoError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    token = credentials.credentials
    user_id_str = decode_access_token(token)
    return int(user_id_str)


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    from app.services.auth_service import get_user_by_id

    user = await get_user_by_id(db, user_id)
    if not user.is_active:
        raise TokenInvalidoError()
    return user
