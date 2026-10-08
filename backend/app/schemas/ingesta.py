"""Schemas Pydantic para los endpoints de ingesta."""

from typing import Literal

from pydantic import BaseModel


class DeteccionPolitica(BaseModel):
    """Si el texto parece una política de privacidad (ver services/deteccion_politica.py)."""

    resultado: Literal["politica", "dudosa", "no_politica"]
    temas_encontrados: list[str]
    temas_total: int
    cobertura: float
    voz_responsable: int


class IngestaResponse(BaseModel):
    texto_procesado: str
    caracteres: int
    palabras: int
    fuente: str
    deteccion: DeteccionPolitica
