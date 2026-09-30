"""Dependencias de FastAPI reutilizables."""

from datetime import datetime, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccesoDenegadoError, TokenInvalidoError
from app.core.security import decode_access_token
from app.core.token_revocation import token_esta_revocado
from app.database import get_db
from app.models.user import ROL_ADMINISTRADOR, User

security = HTTPBearer()


async def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Decodifica y valida firma/expiración del token. No comprueba revocación
    (eso lo hace get_current_user, que sí necesita el jti y la sesión de BD)."""
    return decode_access_token(credentials.credentials)


def _emitido_antes_de_invalidacion(payload: dict, sesiones_validas_desde: datetime | None) -> bool:
    """True si el token es anterior a la última invalidación de todas las sesiones
    del usuario (cambio de contraseña o desactivación de la cuenta). Un token sin
    'iat' no puede demostrar que es posterior, así que también se rechaza."""
    if sesiones_validas_desde is None:
        return False
    if sesiones_validas_desde.tzinfo is None:
        # SQLite (pruebas) devuelve fechas sin zona; se guardan siempre en UTC.
        sesiones_validas_desde = sesiones_validas_desde.replace(tzinfo=timezone.utc)
    iat = payload.get("iat")
    return iat is None or iat < sesiones_validas_desde.timestamp()


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
    if _emitido_antes_de_invalidacion(payload, user.sessions_valid_from):
        raise TokenInvalidoError()
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Restringe la ruta al rol administrador. Usa el rol vigente en la base de
    datos (no el del token), para que un cambio de rol tenga efecto inmediato."""
    if current_user.role != ROL_ADMINISTRADOR:
        raise AccesoDenegadoError()
    return current_user
