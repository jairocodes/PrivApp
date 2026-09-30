"""Repositorio de acceso a datos para el corpus normativo (CorpusChunk)."""

from typing import Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


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

        # Búsqueda exacta (sin índice aproximado, ver la migración 0008): los
        # filtros se aplican antes de ordenar, así que siempre se completan k
        # fragmentos mientras haya suficientes activos.
        sql = text(f"""
            SELECT id, documento_fuente, jurisdiccion, referencia,
                   categoria_tematica, texto_original, metadatos
            FROM   corpus_chunks
            {where_sql}
            ORDER  BY embedding <=> CAST(:embedding AS vector)
            LIMIT  :k
        """)

        result = await self.db.execute(sql, params)
        return result.mappings().all()

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

    async def hashes_existentes(self, hashes: list[str]) -> set[str]:
        """Hashes (metadatos.hash) que ya están en el corpus, para no duplicar fragmentos."""
        if not hashes:
            return set()
        result = await self.db.execute(
            text("SELECT metadatos->>'hash' FROM corpus_chunks WHERE metadatos->>'hash' = ANY(:hashes)"),
            {"hashes": hashes},
        )
        return set(result.scalars().all())

    def agregar(self, fragmento) -> None:
        self.db.add(fragmento)

    async def contar(self) -> int:
        result = await self.db.execute(text("SELECT COUNT(*) FROM corpus_chunks"))
        return result.scalar_one()
