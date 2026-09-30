"""Servicio de autenticación y gestión de usuarios."""

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AvisoNoAceptadoError,
    CredencialesInvalidasError,
    UsuarioNoEncontradoError,
    UsuarioYaExisteError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import ROL_ADMINISTRADOR, ROL_USUARIO, User
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
    acepta_aviso: bool,
) -> tuple[User, str]:
    # La casilla ya se valida en el esquema; el servicio no registra a nadie
    # sin aceptación aunque lo llame otro punto de entrada.
    if not acepta_aviso:
        raise AvisoNoAceptadoError()

    existing = await get_user_by_email(db, email)
    if existing:
        raise UsuarioYaExisteError()

    user = User(
        nombre=nombre,
        email=email,
        hashed_password=hash_password(password),
        # El registro público nunca asigna otro rol.
        role=ROL_USUARIO,
        privacy_accepted_at=datetime.now(timezone.utc),
    )
    RepositorioUsuarios(db).agregar(user)
    await db.flush()

    token = create_access_token(str(user.id), user.role)
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

    token = create_access_token(str(user.id), user.role)
    logger.info("Login exitoso: id=%s", user.id)
    return user, token


async def promover_a_administrador(db: AsyncSession, email: str) -> User:
    """Asigna el rol administrador a un usuario existente. Se usa solo desde
    scripts/promover_admin.py: ninguna ruta de la API permite elevar roles."""
    user = await get_user_by_email(db, email)
    if not user:
        raise UsuarioNoEncontradoError()
    user.role = ROL_ADMINISTRADOR
    await db.flush()
    logger.info("Usuario promovido a administrador: id=%s", user.id)
    return user
