"""Schemas Pydantic de la administración del corpus normativo."""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentoCorpus(BaseModel):
    documento_fuente: str
    jurisdiccion: str
    fragmentos: int
    fecha_carga: datetime | None
    activo: bool


class CambioEstadoDocumentoRequest(BaseModel):
    documento_fuente: str = Field(..., min_length=1, max_length=255)
    activo: bool


class ListadoCorpusResponse(BaseModel):
    documentos: list[DocumentoCorpus]
