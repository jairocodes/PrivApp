"""Schema del request para iniciar un análisis."""

from pydantic import BaseModel, Field

from app.utils.validacion_texto import MAX_CARACTERES


class IniciarAnalisisRequest(BaseModel):
    # Llega ya limpio desde la ingesta; la regla completa (RN-01) la aplica el endpoint.
    texto: str = Field(..., min_length=1, max_length=MAX_CARACTERES)
    # Obligatorio cuando la detección considera el texto dudoso (RN-18).
    confirma_politica: bool = False
