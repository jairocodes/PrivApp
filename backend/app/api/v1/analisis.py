"""Endpoints del Motor de Análisis.

POST /api/analisis/iniciar      — crea el análisis y lo procesa en segundo plano
GET  /api/analisis/{id}/estado  — consulta el progreso de un análisis (HU-13)
GET  /api/analisis/{id}         — devuelve el resultado de un análisis completado
GET  /api/analisis              — lista paginada del historial del usuario
GET  /api/analisis/estadisticas — totales del usuario para el panel estadístico
GET  /api/analisis/{id}/pdf     — descarga el reporte del análisis en PDF
DELETE /api/analisis/{id}       — elimina de forma definitiva un análisis propio
"""

import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_current_user
from app.database import get_db
from app.core.exceptions import RangoFechasInvalidoError
from app.core.limiter import limiter
from app.models.user import User
from app.repositories.analisis import FiltrosHistorial
from app.schemas.analysis import (
    AnalisisEstadoResponse,
    AnalisisIniciadoResponse,
    AnalisisResponse,
    EstadisticasResponse,
    HistorialResponse,
)
from app.schemas.analisis_request import IniciarAnalisisRequest
from app.services.analisis_service import (
    crear_analisis,
    registrar_generacion_reporte,
    eliminar_analisis,
    estadisticas_de_usuario,
    lanzar_analisis_en_fondo,
    listar_historial,
    obtener_analisis,
    obtener_estado_analisis,
)
from app.services.reportes_service import generar_pdf_y_medir
from app.utils.validacion_texto import validar_longitud_politica

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/iniciar", response_model=AnalisisIniciadoResponse, status_code=202)
@limiter.limit("5/minute")
async def iniciar(
    request: Request,
    payload: IniciarAnalisisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalisisIniciadoResponse:
    """Crea el análisis y programa su procesamiento en segundo plano.

    El cliente debe sondear GET /{id}/estado hasta que el análisis esté
    'completado', y luego consultar GET /{id} para el resultado completo.
    """
    # Misma regla que la ingesta, para que no pueda saltarse llamando a la API.
    validar_longitud_politica(payload.texto)
    logger.info(
        "Usuario %d solicitó análisis [%d palabras].",
        current_user.id,
        len(payload.texto.split()),
    )
    registro = await crear_analisis(db, payload.texto, current_user.id)
    lanzar_analisis_en_fondo(registro.id, payload.texto)
    return AnalisisIniciadoResponse(id_analisis=str(registro.id), estado="procesando")


# Debe declararse antes de /{analisis_id} para que "estadisticas" no se tome como id.
@router.get("/estadisticas", response_model=EstadisticasResponse)
async def estadisticas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EstadisticasResponse:
    """Total de análisis del usuario, su distribución por nivel y la puntuación promedio."""
    return await estadisticas_de_usuario(db, current_user.id)


@router.get("/{analisis_id}/estado", response_model=AnalisisEstadoResponse)
async def estado(
    analisis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalisisEstadoResponse:
    """Consulta el progreso de un análisis mientras está en curso."""
    return await obtener_estado_analisis(db, analisis_id, current_user.id)


@router.get("/{analisis_id}", response_model=AnalisisResponse)
async def obtener(
    analisis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    """Recupera el resultado de un análisis ya completado."""
    return await obtener_analisis(db, analisis_id, current_user.id)


def _a_utc(fecha: datetime | None) -> datetime | None:
    """Las fechas sin zona se toman como UTC; todas se comparan en UTC."""
    if fecha is None:
        return None
    return fecha.replace(tzinfo=timezone.utc) if fecha.tzinfo is None else fecha.astimezone(timezone.utc)


@router.get("", response_model=HistorialResponse)
async def listar(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    nivel: Literal["bajo", "medio", "alto"] | None = Query(None, description="Nivel de riesgo global"),
    desde: datetime | None = Query(None, description="Desde esta fecha y hora (ISO 8601, inclusive)"),
    hasta: datetime | None = Query(None, description="Hasta esta fecha y hora (ISO 8601, inclusive)"),
    q: str | None = Query(None, max_length=100, description="Texto en la política o en el resumen"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HistorialResponse:
    """Lista paginada de los análisis del usuario autenticado, más recientes primero."""
    desde, hasta = _a_utc(desde), _a_utc(hasta)
    if desde and hasta and desde > hasta:
        raise RangoFechasInvalidoError()
    texto = q.strip() if q else None
    filtros = FiltrosHistorial(nivel=nivel, desde=desde, hasta=hasta, texto=texto or None)
    return await listar_historial(db, current_user.id, page, page_size, filtros)


@router.get("/{analisis_id}/pdf")
@limiter.limit("10/minute")
async def descargar_pdf(
    request: Request,
    analisis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Genera y descarga el reporte en PDF de un análisis ya completado."""
    analisis = await obtener_analisis(db, analisis_id, current_user.id)
    pdf_bytes, segundos = await run_in_threadpool(generar_pdf_y_medir, analisis)
    try:
        await registrar_generacion_reporte(db, analisis_id, current_user.id, segundos)
    except Exception:
        # La medición nunca debe impedir la descarga del reporte.
        logger.exception("No se pudo registrar el tiempo del reporte del análisis %s.", analisis_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="privapp-analisis-{analisis_id}.pdf"'
        },
    )


@router.delete("/{analisis_id}", status_code=204)
async def eliminar(
    analisis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Elimina de forma definitiva un análisis del usuario autenticado."""
    await eliminar_analisis(db, analisis_id, current_user.id)
    return Response(status_code=204)
