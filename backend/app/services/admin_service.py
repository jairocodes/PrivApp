"""Servicio de administración: gestión de las cuentas de usuario."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AutodesactivacionError, UsuarioNoEncontradoError
from app.models.user import User
from app.repositories.usuarios import RepositorioUsuarios
from app.schemas.admin import ListadoUsuariosResponse, UsuarioAdminItem

logger = logging.getLogger(__name__)


async def listar_usuarios(
    db: AsyncSession,
    page: int,
    page_size: int,
    busqueda: str | None = None,
) -> ListadoUsuariosResponse:
    """Lista paginada de usuarios, con búsqueda opcional por nombre o correo."""
    busqueda = busqueda.strip() if busqueda else None
    repo = RepositorioUsuarios(db)
    total = await repo.contar(busqueda)
    usuarios = await repo.listar(limit=page_size, offset=(page - 1) * page_size, busqueda=busqueda)
    return ListadoUsuariosResponse(
        items=[UsuarioAdminItem.model_validate(u) for u in usuarios],
        total=total,
        page=page,
        page_size=page_size,
    )


async def cambiar_estado_usuario(
    db: AsyncSession,
    admin: User,
    user_id: int,
    activo: bool,
) -> UsuarioAdminItem:
    """Activa o desactiva una cuenta. Al desactivarla se invalidan todas sus
    sesiones vigentes; el inicio de sesión ya rechaza las cuentas inactivas."""
    if user_id == admin.id and not activo:
        raise AutodesactivacionError()

    repo = RepositorioUsuarios(db)
    user = await repo.obtener_por_id(user_id)
    if user is None:
        raise UsuarioNoEncontradoError()

    await repo.cambiar_estado(user, activo)
    if not activo:
        await repo.invalidar_sesiones(user)
    logger.info("Administrador %s cambió el estado del usuario %s a activo=%s.", admin.id, user.id, activo)
    return UsuarioAdminItem.model_validate(user)
