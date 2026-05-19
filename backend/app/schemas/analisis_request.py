"""Schema del request para iniciar un análisis."""

from pydantic import BaseModel, Field


class IniciarAnalisisRequest(BaseModel):
    texto: str = Field(..., min_length=200, max_length=50_000)
