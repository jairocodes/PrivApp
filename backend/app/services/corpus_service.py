"""Servicio de administración del corpus normativo (documentos fuente)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentoCorpusNoEncontradoError
from app.repositories.corpus import RepositorioCorpusNormativo
from app.schemas.corpus import DocumentoCorpus, ListadoCorpusResponse

logger = logging.getLogger(__name__)


async def listar_documentos(db: AsyncSession) -> ListadoCorpusResponse:
    filas = await RepositorioCorpusNormativo(db).listar_documentos()
    return ListadoCorpusResponse(documentos=[DocumentoCorpus(**dict(f)) for f in filas])


async def cambiar_estado_documento(
    db: AsyncSession, documento_fuente: str, activo: bool
) -> DocumentoCorpus:
    """Activa o desactiva el documento completo. No modifica el texto ni las
    representaciones vectoriales de sus fragmentos."""
    repo = RepositorioCorpusNormativo(db)
    if await repo.cambiar_estado_documento(documento_fuente, activo) == 0:
        raise DocumentoCorpusNoEncontradoError()
    logger.info("Documento del corpus '%s' marcado como activo=%s.", documento_fuente, activo)
    return DocumentoCorpus(**dict(await repo.obtener_documento(documento_fuente)))
