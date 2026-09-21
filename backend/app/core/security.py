"""Utilidades de seguridad: hashing de contraseñas y manejo de JWT.

Implementación completa en Sprint 1. Este módulo define la interfaz
que usará el módulo de autenticación.
"""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import TokenInvalidoError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    payload = {"sub": subject, "exp": expire, "jti": str(uuid.uuid4())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decodifica y valida firma/expiración. Devuelve el payload completo
    (incluye 'jti' para poder comprobar revocación en deps.py; los tokens
    emitidos antes de introducir 'jti' no lo tendrán, ver TICKET-03)."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("sub") is None:
            raise TokenInvalidoError()
        return payload
    except JWTError:
        raise TokenInvalidoError()
