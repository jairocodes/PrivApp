"""Endpoints de ingesta de políticas de privacidad.

POST /api/ingesta/texto    — recibe texto pegado directamente
POST /api/ingesta/url      — descarga y extrae texto desde una URL
POST /api/ingesta/archivo  — extrae texto de un archivo PDF o TXT (no se guarda)
"""

import logging
import re

from fastapi import APIRouter, Depends, File, Request, UploadFile
from starlette.concurrency import run_in_threadpool
from starlette.formparsers import MultiPartParser

from app.api.deps import get_current_user
from app.core.exceptions import TextoNoEsPoliticaError
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.analysis import IngestaTextoRequest, IngestaURLRequest
from app.schemas.ingesta import DeteccionPolitica, IngestaResponse
from app.services.deteccion_politica import detectar_politica
from app.services.ingesta_service import (
    TAMANO_MAXIMO_ARCHIVO,
    extraer_texto_url,
    procesar_archivo,
    procesar_texto_directo,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Starlette pasa a un archivo temporal en disco las partes de más de 1 MB.
# Se sube el umbral por encima del tamaño máximo permitido para que un
# archivo válido se procese solo en memoria y nunca se escriba en disco.
MultiPartParser.max_file_size = TAMANO_MAXIMO_ARCHIVO + 1024 * 1024


async def _respuesta_ingesta(texto_limpio: str, fuente: str) -> IngestaResponse:
    """Rechaza el texto que claramente no es una política (RN-18) y, si no,
    devuelve el texto con la detección para que la vista previa avise si es dudoso."""
    # Los embeddings ocupan la CPU: se calculan fuera del bucle de eventos.
    deteccion = await run_in_threadpool(detectar_politica, texto_limpio)
    if deteccion.resultado == "no_politica":
        raise TextoNoEsPoliticaError()
    return IngestaResponse(
        texto_procesado=texto_limpio,
        caracteres=len(texto_limpio),
        palabras=len(texto_limpio.split()),
        fuente=fuente,
        deteccion=DeteccionPolitica(**deteccion.como_dict()),
    )


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
    return await _respuesta_ingesta(texto_limpio, "texto_directo")


@router.post("/url", response_model=IngestaResponse, status_code=200)
@limiter.limit("10/minute")
async def ingestar_url(
    request: Request,
    payload: IngestaURLRequest,
    current_user: User = Depends(get_current_user),
) -> IngestaResponse:
    """Descarga la URL indicada y extrae el texto de la política."""
    texto_limpio = extraer_texto_url(str(payload.url))
    logger.info("Usuario %d ingresó una URL [%d palabras].", current_user.id, len(texto_limpio.split()))
    return await _respuesta_ingesta(texto_limpio, str(payload.url))


@router.post("/archivo", response_model=IngestaResponse, status_code=200)
@limiter.limit("10/minute")
async def ingestar_archivo(
    request: Request,
    archivo: UploadFile = File(..., description="Política en PDF o TXT, máximo 5 MB"),
    current_user: User = Depends(get_current_user),
) -> IngestaResponse:
    """Extrae el texto de un archivo PDF o TXT. El archivo se descarta al terminar."""
    try:
        # Se lee un byte más del máximo para detectar archivos que lo superan.
        contenido = await archivo.read(TAMANO_MAXIMO_ARCHIVO + 1)
    finally:
        await archivo.close()
    # Solo el nombre, sin la ruta que algunos navegadores envían (con / o \).
    nombre = re.split(r"[\\/]", archivo.filename or "")[-1]
    texto_limpio = procesar_archivo(nombre, archivo.content_type, contenido)
    logger.info("Usuario %d cargó un archivo [%d palabras].", current_user.id, len(texto_limpio.split()))
    return await _respuesta_ingesta(texto_limpio, nombre)
