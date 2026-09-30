"""Pruebas de integración del historial contra PostgreSQL (filtros sobre JSONB).

Se ejecutan solo si PRIVAPP_TEST_PG_URL apunta a una base con las migraciones
aplicadas; vacían users y analysis_temp, así que nunca deben apuntar a una base
con datos reales.
"""

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.analysis import AnalysisTemp
from app.models.user import User
from app.repositories.analisis import FiltrosHistorial, RepositorioAnalisis

PG_URL = os.environ.get("PRIVAPP_TEST_PG_URL")

pytestmark = pytest.mark.skipif(not PG_URL, reason="requiere PRIVAPP_TEST_PG_URL (PostgreSQL)")


@pytest.fixture
async def db_pg():
    engine = create_async_engine(PG_URL)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE analysis_temp, users RESTART IDENTITY CASCADE"))
    sesiones = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with sesiones() as sesion:
        yield sesion
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE analysis_temp, users RESTART IDENTITY CASCADE"))
    await engine.dispose()


async def _usuario(db: AsyncSession, email: str) -> User:
    user = User(nombre="Persona", email=email, hashed_password="x", privacy_accepted_at=datetime.now(timezone.utc))
    db.add(user)
    await db.flush()
    return user


def _analisis(user_id: int, nivel: str, comentario: str, **kwargs) -> AnalysisTemp:
    return AnalysisTemp(
        user_id=user_id,
        texto_original=kwargs.pop("texto", "Texto de la política"),
        estado="completado",
        resultado={"resumen_general": {"nivel_riesgo_global": nivel, "puntaje": 50, "comentario_breve": comentario}},
        **kwargs,
    )


class TestFiltrosDelHistorial:
    async def test_filtra_por_nivel_dentro_del_jsonb(self, db_pg):
        ana = await _usuario(db_pg, "ana@privapp.test")
        otro = await _usuario(db_pg, "otro@privapp.test")
        db_pg.add_all([
            _analisis(ana.id, "alto", "A1"),
            _analisis(ana.id, "bajo", "B1"),
            _analisis(otro.id, "alto", "Ajeno"),
        ])
        await db_pg.commit()
        repo = RepositorioAnalisis(db_pg)
        filtros = FiltrosHistorial(nivel="alto")

        registros = await repo.listar_completados_de_usuario(ana.id, 10, 0, filtros)

        assert [r.resultado["resumen_general"]["comentario_breve"] for r in registros] == ["A1"]
        assert await repo.contar_completados_de_usuario(ana.id, filtros) == 1


class TestFiltroPorFechasPg:
    async def test_compara_fechas_con_zona_horaria(self, db_pg):
        from datetime import timedelta

        ana = await _usuario(db_pg, "ana@privapp.test")
        base = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
        db_pg.add_all([
            _analisis(ana.id, "alto", "Antes", created_at=base - timedelta(days=1)),
            _analisis(ana.id, "alto", "Dentro", created_at=base),
        ])
        await db_pg.commit()

        filtros = FiltrosHistorial(desde=base - timedelta(hours=1), hasta=base + timedelta(hours=1))
        registros = await RepositorioAnalisis(db_pg).listar_completados_de_usuario(ana.id, 10, 0, filtros)

        assert [r.resultado["resumen_general"]["comentario_breve"] for r in registros] == ["Dentro"]


class TestFiltroPorTextoPg:
    async def test_busca_en_texto_y_en_el_comentario_jsonb(self, db_pg):
        ana = await _usuario(db_pg, "ana@privapp.test")
        db_pg.add_all([
            _analisis(ana.id, "alto", "Comentario común", texto="Política de TikTok"),
            _analisis(ana.id, "bajo", "Presenta HALLAZGOS graves", texto="Otra política"),
            _analisis(ana.id, "medio", "Nada", texto="Descuento del 1000"),
        ])
        await db_pg.commit()
        repo = RepositorioAnalisis(db_pg)

        async def comentarios(texto):
            registros = await repo.listar_completados_de_usuario(ana.id, 10, 0, FiltrosHistorial(texto=texto))
            return sorted(r.resultado["resumen_general"]["comentario_breve"] for r in registros)

        assert await comentarios("tiktok") == ["Comentario común"]
        assert await comentarios("hallazgos") == ["Presenta HALLAZGOS graves"]
        assert await comentarios("100%") == []


class TestBusquedaSinAcentosPg:
    async def test_unaccent_en_el_texto_y_en_el_comentario(self, db_pg):
        ana = await _usuario(db_pg, "ana@privapp.test")
        db_pg.add_all([
            _analisis(ana.id, "alto", "Uno", texto="Política de conservación"),
            _analisis(ana.id, "bajo", "Se detectó información sensible", texto="Otra"),
        ])
        await db_pg.commit()
        repo = RepositorioAnalisis(db_pg)

        async def comentarios(texto):
            registros = await repo.listar_completados_de_usuario(ana.id, 10, 0, FiltrosHistorial(texto=texto))
            return sorted(r.resultado["resumen_general"]["comentario_breve"] for r in registros)

        assert await comentarios("politica de conservacion") == ["Uno"]
        assert await comentarios("POLÍTICA") == ["Uno"]
        assert await comentarios("detecto informacion") == ["Se detectó información sensible"]
