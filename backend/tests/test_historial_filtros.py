"""Tests de la búsqueda y el filtrado del historial (GET /api/analisis)."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User
from tests.test_reportes import _crear_analisis


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


async def _otro_usuario(db: AsyncSession) -> User:
    user = User(
        nombre="Otra Persona",
        email="otra-historial@privapp.test",
        hashed_password=hash_password("OtraPass123"),
        privacy_accepted_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


async def _historial(client: AsyncClient, user: User, **params) -> dict:
    r = await client.get("/api/analisis", params=params, headers=_auth(user))
    assert r.status_code == 200, r.text
    return r.json()


class TestFiltroPorNivel:
    async def test_devuelve_solo_los_analisis_del_nivel_indicado(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        await _crear_analisis(db_session, seed_user.id, nivel="alto", comentario="A1")
        await _crear_analisis(db_session, seed_user.id, nivel="bajo", comentario="B1")
        await _crear_analisis(db_session, seed_user.id, nivel="alto", comentario="A2")

        datos = await _historial(client, seed_user, nivel="alto")

        assert datos["total"] == 2
        assert {i["comentario_breve"] for i in datos["items"]} == {"A1", "A2"}
        assert all(i["nivel_riesgo_global"] == "alto" for i in datos["items"])

    async def test_nunca_incluye_analisis_de_otros_usuarios(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        otro = await _otro_usuario(db_session)
        await _crear_analisis(db_session, otro.id, nivel="alto", comentario="Ajeno")
        await _crear_analisis(db_session, seed_user.id, nivel="alto", comentario="Propio")

        datos = await _historial(client, seed_user, nivel="alto")

        assert [i["comentario_breve"] for i in datos["items"]] == ["Propio"]

    async def test_la_paginacion_cuenta_solo_los_filtrados(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        for i in range(5):
            await _crear_analisis(db_session, seed_user.id, nivel="medio", comentario=f"M{i}")
        await _crear_analisis(db_session, seed_user.id, nivel="bajo", comentario="B")

        datos = await _historial(client, seed_user, nivel="medio", page=2, page_size=2)

        assert datos["total"] == 5
        assert len(datos["items"]) == 2

    async def test_rechaza_un_nivel_desconocido(self, client: AsyncClient, seed_user: User):
        r = await client.get("/api/analisis", params={"nivel": "critico"}, headers=_auth(seed_user))
        assert r.status_code == 422


class TestFiltroPorFechas:
    async def _tres_analisis(self, db_session, user):
        base = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
        await _crear_analisis(db_session, user.id, fecha=base - timedelta(days=5), comentario="Antiguo")
        await _crear_analisis(db_session, user.id, fecha=base, comentario="Medio")
        await _crear_analisis(db_session, user.id, fecha=base + timedelta(days=5), comentario="Reciente")

    async def test_rango_inclusivo(self, client, db_session, seed_user):
        await self._tres_analisis(db_session, seed_user)

        datos = await _historial(
            client, seed_user, desde="2026-09-10T12:00:00Z", hasta="2026-09-15T12:00:00Z"
        )

        assert [i["comentario_breve"] for i in datos["items"]] == ["Reciente", "Medio"]

    async def test_solo_desde_o_solo_hasta(self, client, db_session, seed_user):
        await self._tres_analisis(db_session, seed_user)

        desde = await _historial(client, seed_user, desde="2026-09-11T00:00:00Z")
        hasta = await _historial(client, seed_user, hasta="2026-09-09T00:00:00Z")

        assert [i["comentario_breve"] for i in desde["items"]] == ["Reciente"]
        assert [i["comentario_breve"] for i in hasta["items"]] == ["Antiguo"]

    async def test_respeta_la_zona_horaria_de_la_fecha(self, client, db_session, seed_user):
        # 10/09 12:00 UTC son las 06:00 del 10/09 en Guatemala (UTC-6).
        await self._tres_analisis(db_session, seed_user)

        datos = await _historial(
            client, seed_user, desde="2026-09-10T00:00:00-06:00", hasta="2026-09-10T23:59:59-06:00"
        )

        assert [i["comentario_breve"] for i in datos["items"]] == ["Medio"]

    async def test_combina_fecha_y_nivel(self, client, db_session, seed_user):
        dia = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
        await _crear_analisis(db_session, seed_user.id, fecha=dia, nivel="alto", comentario="Alto del día")
        await _crear_analisis(db_session, seed_user.id, fecha=dia, nivel="bajo", comentario="Bajo del día")
        await _crear_analisis(db_session, seed_user.id, fecha=dia - timedelta(days=30), nivel="alto", comentario="Alto viejo")

        datos = await _historial(client, seed_user, nivel="alto", desde="2026-09-01T00:00:00Z")

        assert [i["comentario_breve"] for i in datos["items"]] == ["Alto del día"]

    async def test_rango_invertido_se_rechaza(self, client, seed_user):
        r = await client.get(
            "/api/analisis",
            params={"desde": "2026-09-15T00:00:00Z", "hasta": "2026-09-10T00:00:00Z"},
            headers=_auth(seed_user),
        )
        assert r.status_code == 422
        assert r.json()["detail"] == "La fecha inicial no puede ser posterior a la fecha final."

    async def test_fecha_con_formato_invalido_se_rechaza(self, client, seed_user):
        r = await client.get("/api/analisis", params={"desde": "ayer"}, headers=_auth(seed_user))
        assert r.status_code == 422


async def _con_texto(db_session, user, texto: str, comentario: str, **kwargs):
    registro = await _crear_analisis(db_session, user.id, comentario=comentario, **kwargs)
    registro.texto_original = texto
    await db_session.flush()
    return registro


class TestFiltroPorTexto:
    async def test_busca_en_el_texto_de_la_politica(self, client, db_session, seed_user):
        await _con_texto(db_session, seed_user, "Política de privacidad de TikTok", "c1")
        await _con_texto(db_session, seed_user, "Política de privacidad de Spotify", "c2")

        datos = await _historial(client, seed_user, q="tiktok")

        assert [i["comentario_breve"] for i in datos["items"]] == ["c1"]

    async def test_busca_en_el_comentario_del_resumen(self, client, db_session, seed_user):
        await _con_texto(db_session, seed_user, "texto", "Presenta 2 hallazgos de riesgo alto")
        await _con_texto(db_session, seed_user, "texto", "Riesgo bajo en general")

        datos = await _historial(client, seed_user, q="HALLAZGOS")

        assert [i["comentario_breve"] for i in datos["items"]] == ["Presenta 2 hallazgos de riesgo alto"]

    async def test_los_comodines_se_buscan_literalmente(self, client, db_session, seed_user):
        await _con_texto(db_session, seed_user, "Descuento del 100% en datos", "con porcentaje")
        await _con_texto(db_session, seed_user, "Descuento del 1000 en datos", "sin porcentaje")

        porcentaje = await _historial(client, seed_user, q="100%")
        guion = await _historial(client, seed_user, q="_")

        assert [i["comentario_breve"] for i in porcentaje["items"]] == ["con porcentaje"]
        assert guion["total"] == 0

    async def test_un_texto_vacio_no_filtra(self, client, db_session, seed_user):
        await _con_texto(db_session, seed_user, "a", "c1")
        await _con_texto(db_session, seed_user, "b", "c2")

        datos = await _historial(client, seed_user, q="   ")

        assert datos["total"] == 2

    async def test_combina_texto_nivel_y_fecha_solo_en_los_propios(self, client, db_session, seed_user):
        otro = await _otro_usuario(db_session)
        dia = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
        await _con_texto(db_session, seed_user, "Política de TikTok", "propio", nivel="alto", fecha=dia)
        await _con_texto(db_session, seed_user, "Política de TikTok", "otro nivel", nivel="bajo", fecha=dia)
        await _con_texto(db_session, otro, "Política de TikTok", "ajeno", nivel="alto", fecha=dia)

        datos = await _historial(
            client, seed_user, q="tiktok", nivel="alto", desde="2026-09-10T00:00:00Z"
        )

        assert [i["comentario_breve"] for i in datos["items"]] == ["propio"]

    async def test_rechaza_textos_demasiado_largos(self, client, seed_user):
        r = await client.get("/api/analisis", params={"q": "x" * 101}, headers=_auth(seed_user))
        assert r.status_code == 422
