"""Repositorio de acceso a datos para el corpus normativo (CorpusChunk)."""

from typing import Mapping, Sequence

import logging

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RepositorioCorpusNormativo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def buscar_similares(
        self,
        embedding_str: str,
        k: int,
        filtro_jurisdiccion: str | None = None,
        filtro_categoria: str | None = None,
    ) -> Sequence[Mapping]:
        """Búsqueda por similitud coseno (pgvector) sobre los fragmentos activos."""
        where_clauses = ["active = true"]
        params: dict = {"embedding": embedding_str, "k": k}

        if filtro_jurisdiccion:
            where_clauses.append("jurisdiccion = :jurisdiccion")
            params["jurisdiccion"] = filtro_jurisdiccion

        if filtro_categoria:
            where_clauses.append("categoria_tematica = :categoria")
            params["categoria"] = filtro_categoria

        where_sql = "WHERE " + " AND ".join(where_clauses)

        # La consulta exterior reordena por distancia: la búsqueda iterativa
        # (ver _activar_busqueda_iterativa) puede entregar los candidatos
        # ligeramente desordenados.
        sql = text(f"""
            WITH candidatos AS MATERIALIZED (
                SELECT id, documento_fuente, jurisdiccion, referencia,
                       categoria_tematica, texto_original, metadatos,
                       embedding <=> CAST(:embedding AS vector) AS distancia
                FROM   corpus_chunks
                {where_sql}
                ORDER  BY distancia
                LIMIT  :k
            )
            SELECT id, documento_fuente, jurisdiccion, referencia,
                   categoria_tematica, texto_original, metadatos
            FROM   candidatos
            ORDER  BY distancia
        """)

        await self._activar_busqueda_iterativa()
        result = await self.db.execute(sql, params)
        return result.mappings().all()

    async def _activar_busqueda_iterativa(self) -> None:
        """El índice ivfflat aplica los filtros (p. ej. active = true) después de
        recorrer sus listas, así que con documentos desactivados podría devolver
        menos de k fragmentos. La búsqueda iterativa de pgvector >= 0.8 sigue
        recorriendo hasta completarlos. SET LOCAL la limita a la transacción; el
        punto de guardado evita romper la búsqueda con una versión anterior."""
        punto = await self.db.begin_nested()
        try:
            await self.db.execute(text("SET LOCAL ivfflat.iterative_scan = relaxed_order"))
            await punto.commit()
        except DBAPIError:
            await punto.rollback()
            logger.warning("pgvector sin búsqueda iterativa; se usa la búsqueda estándar.")

    _RESUMEN_DOCUMENTO = """
        SELECT documento_fuente,
               MIN(jurisdiccion)  AS jurisdiccion,
               COUNT(*)           AS fragmentos,
               MIN(fecha_carga)   AS fecha_carga,
               BOOL_AND(active)   AS activo
        FROM   corpus_chunks
    """

    async def listar_documentos(self) -> Sequence[Mapping]:
        """Un registro por documento fuente, con su número de fragmentos."""
        result = await self.db.execute(text(
            self._RESUMEN_DOCUMENTO + " GROUP BY documento_fuente ORDER BY documento_fuente"
        ))
        return result.mappings().all()

    async def obtener_documento(self, documento_fuente: str) -> Mapping | None:
        result = await self.db.execute(
            text(self._RESUMEN_DOCUMENTO + " WHERE documento_fuente = :doc GROUP BY documento_fuente"),
            {"doc": documento_fuente},
        )
        return result.mappings().one_or_none()

    async def cambiar_estado_documento(self, documento_fuente: str, activo: bool) -> int:
        """Activa o desactiva todos los fragmentos del documento; devuelve cuántos cambió."""
        result = await self.db.execute(
            text("UPDATE corpus_chunks SET active = :activo WHERE documento_fuente = :doc"),
            {"activo": activo, "doc": documento_fuente},
        )
        return result.rowcount

    async def contar(self) -> int:
        result = await self.db.execute(text("SELECT COUNT(*) FROM corpus_chunks"))
        return result.scalar_one()
