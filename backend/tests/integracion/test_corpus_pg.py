"""Pruebas de integración del corpus normativo contra PostgreSQL con pgvector.

El resto de la suite usa SQLite, que no soporta pgvector ni JSONB. Estas
pruebas se ejecutan solo si PRIVAPP_TEST_PG_URL apunta a una base con las
migraciones aplicadas (alembic upgrade head); vacían corpus_chunks, así que
nunca deben apuntar a una base con datos reales.

    PRIVAPP_TEST_PG_URL=postgresql+asyncpg://usuario:clave@host:5432/base pytest tests/integracion
"""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.corpus import CorpusChunk
from app.repositories.corpus import RepositorioCorpusNormativo

PG_URL = os.environ.get("PRIVAPP_TEST_PG_URL")

pytestmark = pytest.mark.skipif(not PG_URL, reason="requiere PRIVAPP_TEST_PG_URL (PostgreSQL con pgvector)")

DIMENSION = 768


def _vector(cercania: float) -> list[float]:
    """Vector cuya distancia coseno a la consulta crece al bajar `cercania`."""
    v = [0.0] * DIMENSION
    v[0] = cercania
    v[1] = 1.0 - cercania
    return v


CONSULTA = str(_vector(1.0))


@pytest.fixture
async def db_pg():
    engine = create_async_engine(PG_URL)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE corpus_chunks RESTART IDENTITY"))
    sesiones = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with sesiones() as sesion:
        yield sesion
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE corpus_chunks RESTART IDENTITY"))
    await engine.dispose()


async def _insertar(db: AsyncSession, documento: str, cantidad: int, cercania: float) -> None:
    for i in range(cantidad):
        db.add(CorpusChunk(
            documento_fuente=documento,
            jurisdiccion="internacional",
            referencia=f"Art. {i}",
            categoria_tematica="proteccion_datos",
            texto_original=f"{documento} fragmento {i}",
            embedding=_vector(cercania - i * 0.001),
            metadatos={"hash": f"{documento}-{i}"},
        ))
    await db.commit()


class TestRecuperacionSoloActivos:
    async def test_los_fragmentos_nuevos_quedan_activos(self, db_pg):
        await _insertar(db_pg, "nuevo.pdf", 1, 0.9)
        activo = await db_pg.scalar(text("SELECT active FROM corpus_chunks"))
        assert activo is True

    async def test_un_documento_desactivado_no_se_recupera(self, db_pg):
        await _insertar(db_pg, "desactivado.pdf", 30, 0.99)  # el más cercano a la consulta
        await _insertar(db_pg, "activo.pdf", 8, 0.6)
        await db_pg.execute(
            text("UPDATE corpus_chunks SET active = false WHERE documento_fuente = 'desactivado.pdf'")
        )
        await db_pg.commit()

        filas = await RepositorioCorpusNormativo(db_pg).buscar_similares(CONSULTA, k=5)

        assert len(filas) == 5, "debe completar k fragmentos con los documentos activos"
        assert {f["documento_fuente"] for f in filas} == {"activo.pdf"}

    async def test_los_resultados_se_ordenan_por_cercania(self, db_pg):
        await _insertar(db_pg, "lejano.pdf", 3, 0.3)
        await _insertar(db_pg, "cercano.pdf", 3, 0.95)

        filas = await RepositorioCorpusNormativo(db_pg).buscar_similares(CONSULTA, k=6)

        documentos = [f["documento_fuente"] for f in filas]
        assert documentos == ["cercano.pdf"] * 3 + ["lejano.pdf"] * 3
