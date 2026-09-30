"""Schemas Pydantic para los endpoints de ingesta."""

from pydantic import BaseModel


class IngestaResponse(BaseModel):
    texto_procesado: str
    caracteres: int
    palabras: int
    fuente: str
