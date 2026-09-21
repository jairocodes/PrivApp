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
        """Búsqueda por similitud coseno (pgvector) sobre corpus_chunks."""
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

        result = await self.db.execute(sql, params)
        return result.mappings().all()

    async def contar(self) -> int:
        result = await self.db.execute(text("SELECT COUNT(*) FROM corpus_chunks"))
        return result.scalar_one()
