"""Dependencias de FastAPI reutilizables. Autenticación implementada en Sprint 1."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Extrae y valida el JWT, devuelve el ID del usuario autenticado."""
    token = credentials.credentials
    user_id_str = decode_access_token(token)
    return int(user_id_str)
