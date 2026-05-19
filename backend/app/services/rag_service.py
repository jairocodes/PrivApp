"""Servicio RAG — recuperación de fragmentos normativos por similitud semántica.

Flujo por sección de política:
1. encode(texto_seccion) → vector 768D
2. Búsqueda por coseno contra corpus_chunks (pgvector <=>)
3. Filtros opcionales por jurisdicción o categoría temática
4. Devuelve top-k fragmentos con metadatos para construir el prompt
"""

import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corpus import CorpusChunk
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
    query_embedding = encode(query_text)
    embedding_str = "[" + ",".join(f"{x:.6f}" for x in query_embedding) + "]"

    # Construir consulta SQL con operador pgvector <=> (distancia coseno)
    where_clauses = []
    params: dict = {"embedding": embedding_str, "k": k}

    if filtro_jurisdiccion:
        where_clauses.append("jurisdiccion = :jurisdiccion")
        params["jurisdiccion"] = filtro_jurisdiccion

    if filtro_categoria:
        where_clauses.append("categoria_tematica = :categoria")
        params["categoria"] = filtro_categoria

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = text(f"""
        SELECT id, documento_fuente, jurisdiccion, referencia,
               categoria_tematica, texto_original, metadatos
        FROM   corpus_chunks
        {where_sql}
        ORDER  BY embedding <=> CAST(:embedding AS vector)
        LIMIT  :k
    """)

    result = await db.execute(sql, params)
    filas = result.mappings().all()

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
    result = await db.execute(text("SELECT COUNT(*) FROM corpus_chunks"))
    return result.scalar_one()
