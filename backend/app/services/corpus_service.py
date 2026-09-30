"""Servicio de administración del corpus normativo (documentos fuente)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.corpus import RepositorioCorpusNormativo
from app.schemas.corpus import DocumentoCorpus, ListadoCorpusResponse

logger = logging.getLogger(__name__)


async def listar_documentos(db: AsyncSession) -> ListadoCorpusResponse:
    filas = await RepositorioCorpusNormativo(db).listar_documentos()
    return ListadoCorpusResponse(documentos=[DocumentoCorpus(**dict(f)) for f in filas])
