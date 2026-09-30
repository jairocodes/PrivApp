"""Endpoints de administración (solo rol administrador).

GET /api/admin/usuarios — lista paginada de usuarios, con búsqueda
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.schemas.admin import ListadoUsuariosResponse
from app.services.admin_service import listar_usuarios

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/usuarios", response_model=ListadoUsuariosResponse)
async def listar(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    q: str | None = Query(None, max_length=100, description="Busca por nombre o correo"),
    db: AsyncSession = Depends(get_db),
) -> ListadoUsuariosResponse:
    """Lista las cuentas de usuario, ordenadas por id."""
    return await listar_usuarios(db, page, page_size, q)
