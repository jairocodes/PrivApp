"""Tests del panel estadístico personal (GET /api/analisis/estadisticas)."""

import pytest

from tests.test_historial_filtros import _auth, _otro_usuario
from tests.test_reportes import _crear_analisis


async def _estadisticas(client, user) -> dict:
    r = await client.get("/api/analisis/estadisticas", headers=_auth(user))
    assert r.status_code == 200, r.text
    return r.json()


class TestEstadisticasPersonales:
    async def test_usuario_sin_analisis_recibe_ceros(self, client, seed_user):
        assert await _estadisticas(client, seed_user) == {
            "total": 0,
            "por_nivel": {"bajo": 0, "medio": 0, "alto": 0},
            "puntaje_promedio": 0,
        }

    async def test_los_totales_coinciden_con_sus_analisis(self, client, db_session, seed_user):
        for nivel, puntaje in [("alto", 90), ("alto", 80), ("medio", 40), ("bajo", 10)]:
            await _crear_analisis(db_session, seed_user.id, nivel=nivel, puntaje=puntaje)

        datos = await _estadisticas(client, seed_user)

        assert datos["total"] == 4
        assert datos["por_nivel"] == {"bajo": 1, "medio": 1, "alto": 2}
        assert datos["puntaje_promedio"] == pytest.approx(55.0)

    async def test_solo_cuenta_los_analisis_completados_propios(self, client, db_session, seed_user):
        otro = await _otro_usuario(db_session)
        await _crear_analisis(db_session, seed_user.id, nivel="medio", puntaje=50)
        await _crear_analisis(db_session, seed_user.id, estado="procesando")
        await _crear_analisis(db_session, seed_user.id, estado="error")
        await _crear_analisis(db_session, otro.id, nivel="alto", puntaje=100)

        datos = await _estadisticas(client, seed_user)

        assert datos["total"] == 1
        assert datos["por_nivel"] == {"bajo": 0, "medio": 1, "alto": 0}
        assert datos["puntaje_promedio"] == 50

    async def test_redondea_el_promedio_a_un_decimal(self, client, db_session, seed_user):
        for puntaje in (10, 10, 11):
            await _crear_analisis(db_session, seed_user.id, nivel="bajo", puntaje=puntaje)

        datos = await _estadisticas(client, seed_user)

        assert datos["puntaje_promedio"] == 10.3

    async def test_no_se_confunde_con_el_detalle_de_un_analisis(self, client, seed_user):
        r = await client.get("/api/analisis/estadisticas", headers=_auth(seed_user))
        assert r.status_code == 200

    async def test_requiere_sesion(self, client):
        r = await client.get("/api/analisis/estadisticas")
        assert r.status_code == 403
