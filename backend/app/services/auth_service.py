"""Servicio de autenticación y gestión de usuarios."""

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AvisoNoAceptadoError,
    CredencialesInvalidasError,
    CuentaConAnalisisEnCursoError,
    PasswordActualIncorrectaError,
    PasswordIncorrectaError,
    PasswordRepetidaError,
    UltimoAdministradorError,
    UsuarioNoEncontradoError,
    UsuarioYaExisteError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import ROL_ADMINISTRADOR, ROL_USUARIO, User
from app.repositories.analisis import RepositorioAnalisis
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


async def actualizar_perfil(db: AsyncSession, user: User, nombre: str) -> User:
    """Actualiza el nombre del usuario autenticado."""
    await RepositorioUsuarios(db).actualizar_perfil(user, nombre)
    logger.info("Perfil actualizado: id=%s", user.id)
    return user


async def cambiar_password(
    db: AsyncSession,
    user: User,
    password_actual: str,
    password_nueva: str,
) -> str:
    """Cambia la contraseña, invalida todas las sesiones del usuario y devuelve
    un token nuevo para que la sesión desde la que se hizo el cambio continúe."""
    if not verify_password(password_actual, user.hashed_password):
        logger.warning("Cambio de contraseña rechazado (actual incorrecta): id=%s", user.id)
        raise PasswordActualIncorrectaError()
    if verify_password(password_nueva, user.hashed_password):
        raise PasswordRepetidaError()

    repo = RepositorioUsuarios(db)
    await repo.actualizar_password(user, hash_password(password_nueva))
    await repo.invalidar_sesiones(user)
    logger.info("Contraseña cambiada y sesiones invalidadas: id=%s", user.id)
    # Se emite después de invalidar: su 'iat' es posterior a sessions_valid_from.
    return create_access_token(str(user.id), user.role)


async def eliminar_cuenta(db: AsyncSession, user: User, password: str) -> None:
    """Elimina de forma definitiva la cuenta del usuario y todos sus análisis.
    Pide la contraseña, no deja al sistema sin administradores y espera a que
    no haya análisis en curso (la tarea de fondo escribiría sobre un registro
    eliminado)."""
    if not verify_password(password, user.hashed_password):
        logger.warning("Eliminación de cuenta rechazada (contraseña incorrecta): id=%s", user.id)
        raise PasswordIncorrectaError()

    usuarios = RepositorioUsuarios(db)
    if user.role == ROL_ADMINISTRADOR and await usuarios.contar_administradores_activos() <= 1:
        raise UltimoAdministradorError()

    analisis = RepositorioAnalisis(db)
    if await analisis.tiene_analisis_en_proceso(user.id):
        raise CuentaConAnalisisEnCursoError()

    eliminados = await analisis.eliminar_de_usuario(user.id)
    user_id = user.id
    await usuarios.eliminar(user)
    logger.info("Cuenta eliminada: id=%s (%d análisis).", user_id, eliminados)
