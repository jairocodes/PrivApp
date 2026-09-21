"""Servicio RAG — recuperación de fragmentos normativos por similitud semántica.

Flujo por sección de política:
1. encode(texto_seccion) → vector 768D
2. Búsqueda por coseno contra corpus_chunks (pgvector <=>)
3. Filtros opcionales por jurisdicción o categoría temática
4. Devuelve top-k fragmentos con metadatos para construir el prompt
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corpus import CorpusChunk
from app.repositories.corpus import RepositorioCorpusNormativo
from app.utils.embeddings import encode

logger = logging.getLogger(__name__)


async def recuperar_contexto(
    db: AsyncSession,
    query_text: str,
    k: int = 5,
    filtro_jurisdiccion: str | None = None,
    filtro_categoria: str | None = None,
) -> list[CorpusChunk]:
    """Recupera los k fragmentos normativos más relevantes para el texto dado.

    Args:
        db: Sesión async de SQLAlchemy.
        query_text: Texto de la sección de la política a analizar.
        k: Número de fragmentos a recuperar.
        filtro_jurisdiccion: Si se provee, limita la búsqueda a esa jurisdicción.
        filtro_categoria: Si se provee, limita por categoría temática.

    Returns:
        Lista de CorpusChunk ordenados por relevancia (mayor similitud primero).
    """
    # encode() carga el modelo de embeddings (~sentence-transformers) y hace
    # inferencia en CPU de forma síncrona; se corre en un hilo aparte para no
    # bloquear el event loop mientras otras requests (ej. GET /estado, HU-13)
    # necesitan seguir respondiendo mientras el análisis avanza en segundo plano.
    query_embedding = await asyncio.to_thread(encode, query_text)
    embedding_str = "[" + ",".join(f"{x:.6f}" for x in query_embedding) + "]"

    repo = RepositorioCorpusNormativo(db)
    filas = await repo.buscar_similares(embedding_str, k, filtro_jurisdiccion, filtro_categoria)

    chunks = [
        CorpusChunk(
            id=fila["id"],
            documento_fuente=fila["documento_fuente"],
            jurisdiccion=fila["jurisdiccion"],
            referencia=fila["referencia"],
            categoria_tematica=fila["categoria_tematica"],
            texto_original=fila["texto_original"],
            metadatos=fila["metadatos"],
        )
        for fila in filas
    ]

    logger.debug(
        "RAG: recuperados %d/%d fragmentos para query '%s...' (jur=%s, cat=%s)",
        len(chunks), k, query_text[:60], filtro_jurisdiccion, filtro_categoria,
    )
    return chunks


async def contar_chunks(db: AsyncSession) -> int:
    """Devuelve la cantidad total de chunks cargados en el corpus."""
    return await RepositorioCorpusNormativo(db).contar()
