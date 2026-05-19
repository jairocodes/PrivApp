"""Endpoints del Motor de Análisis.

POST /api/analisis/iniciar  — recibe texto limpio e inicia el análisis
GET  /api/analisis/{id}     — devuelve el resultado de un análisis
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.analysis import AnalisisResponse
from app.schemas.analisis_request import IniciarAnalisisRequest
from app.services.analisis_service import iniciar_analisis, obtener_analisis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/iniciar", response_model=AnalisisResponse, status_code=201)
@limiter.limit("5/minute")
async def iniciar(
    request: Request,
    payload: IniciarAnalisisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    """Inicia el análisis de una política. Puede tardar varios segundos."""
    logger.info(
        "Usuario %d solicitó análisis [%d palabras].",
        current_user.id,
        len(payload.texto.split()),
    )
    return await iniciar_analisis(db, payload.texto, current_user.id)


@router.get("/{analisis_id}", response_model=AnalisisResponse)
async def obtener(
    analisis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    """Recupera el resultado de un análisis ya completado."""
    return await obtener_analisis(db, analisis_id, current_user.id)
