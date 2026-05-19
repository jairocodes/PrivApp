"""Endpoints de ingesta de políticas de privacidad.

POST /api/ingesta/texto  — recibe texto pegado directamente
POST /api/ingesta/url    — descarga y extrae texto desde una URL
"""

import logging

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.analysis import IngestaTextoRequest, IngestaURLRequest
from app.schemas.ingesta import IngestaResponse
from app.services.ingesta_service import extraer_texto_url, procesar_texto_directo

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/texto", response_model=IngestaResponse, status_code=200)
@limiter.limit("20/minute")
async def ingestar_texto(
    request: Request,
    payload: IngestaTextoRequest,
    current_user: User = Depends(get_current_user),
) -> IngestaResponse:
    """Recibe texto pegado y lo normaliza para análisis posterior."""
    texto_limpio = procesar_texto_directo(payload.texto)
    logger.info("Usuario %d ingresó texto directo [%d palabras].", current_user.id, len(texto_limpio.split()))
    return IngestaResponse(
        texto_procesado=texto_limpio,
        palabras=len(texto_limpio.split()),
        fuente="texto_directo",
    )


@router.post("/url", response_model=IngestaResponse, status_code=200)
@limiter.limit("10/minute")
async def ingestar_url(
    request: Request,
    payload: IngestaURLRequest,
    current_user: User = Depends(get_current_user),
) -> IngestaResponse:
    """Descarga la URL indicada y extrae el texto de la política."""
    texto_limpio = extraer_texto_url(str(payload.url))
    logger.info("Usuario %d ingresó URL '%s' [%d palabras].", current_user.id, payload.url, len(texto_limpio.split()))
    return IngestaResponse(
        texto_procesado=texto_limpio,
        palabras=len(texto_limpio.split()),
        fuente=str(payload.url),
    )
