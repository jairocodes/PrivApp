"""Servicio de administración: gestión de las cuentas de usuario."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.usuarios import RepositorioUsuarios
from app.schemas.admin import ListadoUsuariosResponse, UsuarioAdminItem


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
