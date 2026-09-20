"""Schemas Pydantic para análisis de políticas de privacidad. Implementación en Sprint 4."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FuenteNormativa(BaseModel):
    documento: str
    referencia: str
    fragmento_relevante: str


class Hallazgo(BaseModel):
    tipo: Literal["riesgo", "transparencia", "neutral"]
    descripcion: str
    nivel: Literal["bajo", "medio", "alto"]
    fuentes_normativas: list[FuenteNormativa]


class SeccionAnalizada(BaseModel):
    categoria_opp115: str
    titulo: str
    texto_original: str
    hallazgos: list[Hallazgo]


class ResumenGeneral(BaseModel):
    nivel_riesgo_global: Literal["bajo", "medio", "alto"]
    puntaje: int = Field(..., ge=0, le=100)
    comentario_breve: str


class AnalisisResponse(BaseModel):
    id_analisis: str
    fecha: datetime
    resumen_general: ResumenGeneral
    secciones_analizadas: list[SeccionAnalizada]
    recomendaciones: list[str]


class AnalisisHistorialItem(BaseModel):
    id_analisis: str
    fecha: datetime
    nivel_riesgo_global: Literal["bajo", "medio", "alto"]
    puntaje: int
    comentario_breve: str


class HistorialResponse(BaseModel):
    items: list[AnalisisHistorialItem]
    total: int
    page: int
    page_size: int


class AnalisisIniciadoResponse(BaseModel):
    id_analisis: str
    estado: Literal["procesando"]


class AnalisisEstadoResponse(BaseModel):
    estado: Literal["procesando", "completado", "error"]
    seccion_actual: int
    secciones_total: int | None


class IngestaTextoRequest(BaseModel):
    texto: str = Field(..., min_length=200, max_length=200_000)


class IngestaURLRequest(BaseModel):
    url: str = Field(..., min_length=10)
