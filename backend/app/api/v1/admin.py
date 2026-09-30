"""Endpoints de administración (solo rol administrador).

GET   /api/admin/usuarios              — lista paginada de usuarios, con búsqueda
PATCH /api/admin/usuarios/{id}/estado  — activa o desactiva una cuenta
GET   /api/admin/corpus                — documentos del corpus normativo
PATCH /api/admin/corpus/estado         — activa o desactiva un documento completo
POST  /api/admin/corpus                — incorpora un documento normativo nuevo
"""

import re
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.limiter import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.admin import CambioEstadoUsuarioRequest, ListadoUsuariosResponse, UsuarioAdminItem
from app.schemas.corpus import (
    CambioEstadoDocumentoRequest,
    DocumentoCargadoResponse,
    DocumentoCorpus,
    ListadoCorpusResponse,
)
from app.services.ingesta_service import TAMANO_MAXIMO_ARCHIVO
from app.services import corpus_service
from app.services.admin_service import cambiar_estado_usuario, listar_usuarios

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


@router.patch("/usuarios/{user_id}/estado", response_model=UsuarioAdminItem)
async def cambiar_estado(
    user_id: int,
    body: CambioEstadoUsuarioRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UsuarioAdminItem:
    """Activa o desactiva una cuenta; un administrador no puede desactivarse a sí mismo."""
    return await cambiar_estado_usuario(db, admin, user_id, body.activo)


@router.get("/corpus", response_model=ListadoCorpusResponse)
async def listar_corpus(db: AsyncSession = Depends(get_db)) -> ListadoCorpusResponse:
    """Documentos fuente del corpus, con jurisdicción, fragmentos, fecha y estado."""
    return await corpus_service.listar_documentos(db)


@router.patch("/corpus/estado", response_model=DocumentoCorpus)
async def cambiar_estado_corpus(
    body: CambioEstadoDocumentoRequest,
    db: AsyncSession = Depends(get_db),
) -> DocumentoCorpus:
    """Activa o desactiva todos los fragmentos de un documento fuente."""
    return await corpus_service.cambiar_estado_documento(db, body.documento_fuente, body.activo)


@router.post("/corpus", response_model=DocumentoCargadoResponse, status_code=201)
# Cada carga genera representaciones vectoriales, un trabajo pesado para el servidor.
@limiter.limit("5/minute")
async def cargar_documento_corpus(
    request: Request,
    archivo: UploadFile = File(..., description="Documento normativo en PDF o TXT, máximo 5 MB"),
    jurisdiccion: Literal["guatemala", "internacional", "estandar_tecnico"] = Form(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentoCargadoResponse:
    """Segmenta el documento, genera sus representaciones vectoriales y lo deja
    disponible (activo) para la recuperación semántica."""
    try:
        contenido = await archivo.read(TAMANO_MAXIMO_ARCHIVO + 1)
    finally:
        await archivo.close()
    nombre = re.split(r"[\\/]", archivo.filename or "")[-1]
    return await corpus_service.cargar_documento(db, nombre, archivo.content_type, contenido, jurisdiccion)
