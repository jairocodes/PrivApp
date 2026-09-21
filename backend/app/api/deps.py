"""Dependencias de FastAPI reutilizables."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TokenInvalidoError
from app.core.security import decode_access_token
from app.core.token_revocation import token_esta_revocado
from app.database import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Decodifica y valida firma/expiración del token. No comprueba revocación
    (eso lo hace get_current_user, que sí necesita el jti y la sesión de BD)."""
    return decode_access_token(credentials.credentials)


async def get_current_user_id(
    payload: dict = Depends(get_current_token_payload),
) -> int:
    return int(payload["sub"])


async def get_current_user(
    payload: dict = Depends(get_current_token_payload),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    from app.services.auth_service import get_user_by_id

    jti = payload.get("jti")
    if jti is not None and await token_esta_revocado(jti):
        raise TokenInvalidoError()

    user = await get_user_by_id(db, user_id)
    if not user.is_active:
        raise TokenInvalidoError()
    return user
