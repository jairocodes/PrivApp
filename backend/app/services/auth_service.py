"""Servicio de autenticación y gestión de usuarios."""

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CredencialesInvalidasError,
    UsuarioNoEncontradoError,
    UsuarioYaExisteError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.usuarios import RepositorioUsuarios

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await RepositorioUsuarios(db).obtener_por_email(email)


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    user = await RepositorioUsuarios(db).obtener_por_id(user_id)
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
        # Provisional: la aceptación explícita del aviso (casilla validada en
        # el servidor) se incorpora al registro junto con la página del aviso.
        privacy_accepted_at=datetime.now(timezone.utc),
    )
    RepositorioUsuarios(db).agregar(user)
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
