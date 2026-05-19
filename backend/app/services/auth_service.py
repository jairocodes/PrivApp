"""Servicio de autenticación y gestión de usuarios."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CredencialesInvalidasError,
    UsuarioNoEncontradoError,
    UsuarioYaExisteError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UsuarioNoEncontradoError()
    return user


async def register_user(
    db: AsyncSession,
    nombre: str,
    email: str,
    password: str,
) -> tuple[User, str]:
    existing = await get_user_by_email(db, email)
    if existing:
        raise UsuarioYaExisteError()

    user = User(
        nombre=nombre,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()

    token = create_access_token(str(user.id))
    logger.info("Usuario registrado: id=%s email=%s", user.id, user.email)
    return user, token


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str]:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Intento de login fallido para email=%s", email)
        raise CredencialesInvalidasError()

    if not user.is_active:
        raise CredencialesInvalidasError()

    token = create_access_token(str(user.id))
    logger.info("Login exitoso: id=%s", user.id)
    return user, token
