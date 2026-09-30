"""Schemas Pydantic de la administración del corpus normativo."""

from datetime import datetime

from pydantic import BaseModel


class DocumentoCorpus(BaseModel):
    documento_fuente: str
    jurisdiccion: str
    fragmentos: int
    fecha_carga: datetime | None
    activo: bool


class ListadoCorpusResponse(BaseModel):
    documentos: list[DocumentoCorpus]
