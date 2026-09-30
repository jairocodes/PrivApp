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
