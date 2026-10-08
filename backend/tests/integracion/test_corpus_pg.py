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


class TestListadoDeDocumentos:
    async def test_agrupa_por_documento_fuente(self, db_pg):
        await _insertar(db_pg, "RGPD.pdf", 4, 0.9)
        await _insertar(db_pg, "LOPDP.pdf", 2, 0.8)
        await db_pg.execute(text("UPDATE corpus_chunks SET active = false WHERE documento_fuente = 'LOPDP.pdf'"))
        await db_pg.commit()

        documentos = await RepositorioCorpusNormativo(db_pg).listar_documentos()

        resumen = {d["documento_fuente"]: (d["fragmentos"], d["activo"]) for d in documentos}
        assert resumen == {"LOPDP.pdf": (2, False), "RGPD.pdf": (4, True)}
        assert all(d["jurisdiccion"] == "internacional" and d["fecha_carga"] for d in documentos)


class TestCambioDeEstadoDeDocumentos:
    async def test_desactivar_y_reactivar_un_documento_completo(self, db_pg):
        await _insertar(db_pg, "RGPD.pdf", 3, 0.95)
        await _insertar(db_pg, "LOPDP.pdf", 3, 0.5)
        repo = RepositorioCorpusNormativo(db_pg)

        assert await repo.cambiar_estado_documento("RGPD.pdf", False) == 3
        await db_pg.commit()
        filas = await repo.buscar_similares(CONSULTA, k=6)
        assert {f["documento_fuente"] for f in filas} == {"LOPDP.pdf"}
        assert (await repo.obtener_documento("RGPD.pdf"))["activo"] is False

        assert await repo.cambiar_estado_documento("RGPD.pdf", True) == 3
        await db_pg.commit()
        filas = await repo.buscar_similares(CONSULTA, k=6)
        assert [f["documento_fuente"] for f in filas][:3] == ["RGPD.pdf"] * 3

    async def test_el_cambio_no_toca_el_texto_ni_los_vectores(self, db_pg):
        await _insertar(db_pg, "RGPD.pdf", 2, 0.9)
        antes = (await db_pg.execute(text(
            "SELECT id, texto_original, embedding::text FROM corpus_chunks ORDER BY id"
        ))).all()

        await RepositorioCorpusNormativo(db_pg).cambiar_estado_documento("RGPD.pdf", False)
        await db_pg.commit()

        despues = (await db_pg.execute(text(
            "SELECT id, texto_original, embedding::text FROM corpus_chunks ORDER BY id"
        ))).all()
        assert despues == antes

    async def test_documento_inexistente_no_cambia_nada(self, db_pg):
        await _insertar(db_pg, "RGPD.pdf", 1, 0.9)
        assert await RepositorioCorpusNormativo(db_pg).cambiar_estado_documento("otro.pdf", False) == 0


def _embeddings_falsos(textos):
    """Evita cargar el modelo real: vectores distintos y deterministas."""
    return [_vector(0.5 + (hash(t) % 400) / 1000) for t in textos]


TEXTO_NORMA = " ".join(
    f"Artículo {i}. El responsable del tratamiento deberá informar al titular sobre la finalidad "
    f"de la recopilación de sus datos personales y los derechos que le asisten."
    for i in range(40)
)


class TestCargaDeDocumentos:
    async def test_insertar_fragmentos_y_deduplicar_por_hash(self, db_pg):
        from unittest.mock import patch

        from app.services.corpus_service import insertar_fragmentos

        with patch("app.services.corpus_service.encode_batch", _embeddings_falsos):
            insertados, duplicados = await insertar_fragmentos(db_pg, "Norma.pdf", TEXTO_NORMA, "guatemala")
            await db_pg.commit()
            otra_vez = await insertar_fragmentos(db_pg, "Norma.pdf", TEXTO_NORMA, "guatemala")

        assert insertados > 1 and duplicados == 0
        assert otra_vez == (0, insertados)
        fila = (await db_pg.execute(text(
            "SELECT jurisdiccion, referencia, active, metadatos->>'hash' FROM corpus_chunks LIMIT 1"
        ))).one()
        assert fila[0] == "guatemala" and fila[1] == "Norma" and fila[2] is True and fila[3]

    async def test_un_documento_cargado_participa_en_la_recuperacion(self, db_pg):
        from unittest.mock import patch

        from app.services.corpus_service import cargar_documento

        with patch("app.services.corpus_service.encode_batch", _embeddings_falsos):
            respuesta = await cargar_documento(
                db_pg, "Norma cargada.txt", "text/plain", TEXTO_NORMA.encode(), "guatemala"
            )
            await db_pg.commit()

        assert respuesta.activo is True
        assert respuesta.fragmentos == respuesta.fragmentos_insertados > 1
        filas = await RepositorioCorpusNormativo(db_pg).buscar_similares(CONSULTA, k=3)
        assert {f["documento_fuente"] for f in filas} == {"Norma cargada.txt"}


class TestBusquedaExacta:
    async def test_no_hay_indice_aproximado_sobre_los_vectores(self, db_pg):
        indices = (await db_pg.execute(text(
            "SELECT indexdef FROM pg_indexes WHERE tablename = 'corpus_chunks'"
        ))).scalars().all()
        assert not any("ivfflat" in i or "hnsw" in i for i in indices)


class TestRecuperacionReproducible:
    async def test_las_distancias_iguales_se_desempatan_por_id(self, db_pg):
        for i in range(4):
            db_pg.add(CorpusChunk(
                documento_fuente="empate.pdf", jurisdiccion="internacional", referencia=f"Art. {i}",
                categoria_tematica="proteccion_datos", texto_original=f"empate {i}",
                embedding=_vector(0.8), metadatos={"hash": f"empate-{i}"},
            ))
        await db_pg.commit()

        filas = await RepositorioCorpusNormativo(db_pg).buscar_similares(CONSULTA, k=4)

        assert [f["id"] for f in filas] == sorted(f["id"] for f in filas)

    async def test_la_huella_cambia_al_desactivar_un_documento(self, db_pg):
        await _insertar(db_pg, "RGPD.pdf", 2, 0.9)
        await _insertar(db_pg, "LOPDP.pdf", 2, 0.8)
        repo = RepositorioCorpusNormativo(db_pg)

        inicial = await repo.huella_fragmentos_activos()
        assert await repo.huella_fragmentos_activos() == inicial

        await repo.cambiar_estado_documento("LOPDP.pdf", False)
        await db_pg.commit()
        desactivado = await repo.huella_fragmentos_activos()

        await repo.cambiar_estado_documento("LOPDP.pdf", True)
        await db_pg.commit()

        assert desactivado != inicial
        assert await repo.huella_fragmentos_activos() == inicial
