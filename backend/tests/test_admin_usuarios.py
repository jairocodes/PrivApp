"""Tests de la administración de usuarios (listado y cambio de estado)."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.analysis import AnalysisTemp
from app.models.user import ROL_ADMINISTRADOR, User


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _crear_usuario(db: AsyncSession, nombre: str, email: str) -> User:
    user = User(
        nombre=nombre,
        email=email,
        hashed_password=hash_password("OtraPass123"),
        privacy_accepted_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


@pytest.fixture
async def admin(db_session: AsyncSession, seed_user: User) -> User:
    seed_user.role = ROL_ADMINISTRADOR
    await db_session.flush()
    return seed_user


@pytest.fixture
def token_admin(admin: User) -> str:
    return create_access_token(str(admin.id), ROL_ADMINISTRADOR)


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------

class TestListadoDeUsuarios:
    async def test_usuario_comun_recibe_403(self, client: AsyncClient, seed_user: User):
        r = await client.get("/api/admin/usuarios", headers=_auth(create_access_token(str(seed_user.id))))
        assert r.status_code == 403

    async def test_administrador_obtiene_el_listado_con_los_datos_de_la_cuenta(
        self, client: AsyncClient, db_session: AsyncSession, admin: User, token_admin: str
    ):
        otro = await _crear_usuario(db_session, "Luis Pérez", "luis@privapp.test")

        r = await client.get("/api/admin/usuarios", headers=_auth(token_admin))

        assert r.status_code == 200
        datos = r.json()
        assert datos["total"] == 2
        assert [u["id"] for u in datos["items"]] == [admin.id, otro.id]
        assert set(datos["items"][1]) == {"id", "nombre", "email", "role", "is_active", "created_at"}
        assert datos["items"][1]["role"] == "usuario"
        assert datos["items"][1]["is_active"] is True

    async def test_el_listado_no_expone_el_contenido_de_los_analisis(
        self, client: AsyncClient, db_session: AsyncSession, token_admin: str
    ):
        otro = await _crear_usuario(db_session, "Luis Pérez", "luis@privapp.test")
        db_session.add(AnalysisTemp(
            user_id=otro.id,
            texto_original="Contenido privado de la política",
            estado="completado",
            resultado={"secreto": "no debe verse"},
        ))
        await db_session.flush()

        r = await client.get("/api/admin/usuarios", headers=_auth(token_admin))

        assert "Contenido privado" not in r.text
        assert "no debe verse" not in r.text

    async def test_pagina_el_listado(
        self, client: AsyncClient, db_session: AsyncSession, token_admin: str
    ):
        for i in range(4):
            await _crear_usuario(db_session, f"Usuario {i}", f"u{i}@privapp.test")

        r = await client.get("/api/admin/usuarios?page=2&page_size=2", headers=_auth(token_admin))

        datos = r.json()
        assert datos["total"] == 5
        assert datos["page"] == 2
        assert [u["email"] for u in datos["items"]] == ["u1@privapp.test", "u2@privapp.test"]

    @pytest.mark.parametrize("busqueda", ["luis", "LUIS@PRIV"])
    async def test_busca_por_nombre_o_correo_sin_distinguir_mayusculas(
        self, client: AsyncClient, db_session: AsyncSession, token_admin: str, busqueda: str
    ):
        await _crear_usuario(db_session, "Luis Pérez", "luis@privapp.test")
        await _crear_usuario(db_session, "María López", "maria@privapp.test")

        r = await client.get(f"/api/admin/usuarios?q={busqueda}", headers=_auth(token_admin))

        datos = r.json()
        assert datos["total"] == 1
        assert datos["items"][0]["email"] == "luis@privapp.test"

    async def test_rechaza_paginas_demasiado_grandes(self, client: AsyncClient, token_admin: str):
        r = await client.get("/api/admin/usuarios?page_size=51", headers=_auth(token_admin))
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Activación y desactivación
# ---------------------------------------------------------------------------

async def _cambiar_estado(client: AsyncClient, token: str, user_id: int, activo: bool):
    return await client.patch(
        f"/api/admin/usuarios/{user_id}/estado", json={"activo": activo}, headers=_auth(token)
    )


class TestCambioDeEstado:
    async def test_usuario_comun_recibe_403(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        otro = await _crear_usuario(db_session, "Luis Pérez", "luis@ejemplo.com")
        r = await _cambiar_estado(client, create_access_token(str(seed_user.id)), otro.id, False)
        assert r.status_code == 403

    async def test_desactivar_bloquea_la_sesion_vigente_y_el_inicio_de_sesion(
        self, client: AsyncClient, db_session: AsyncSession, token_admin: str
    ):
        otro = await _crear_usuario(db_session, "Luis Pérez", "luis@ejemplo.com")
        token_otro = create_access_token(str(otro.id))
        assert (await client.get("/api/auth/me", headers=_auth(token_otro))).status_code == 200

        r = await _cambiar_estado(client, token_admin, otro.id, False)

        assert r.status_code == 200
        assert r.json()["is_active"] is False
        assert otro.sessions_valid_from is not None
        assert (await client.get("/api/auth/me", headers=_auth(token_otro))).status_code == 401
        login = await client.post(
            "/api/auth/login", json={"email": "luis@ejemplo.com", "password": "OtraPass123"}
        )
        assert login.status_code == 401

    async def test_reactivar_permite_iniciar_sesion_de_nuevo(
        self, client: AsyncClient, db_session: AsyncSession, token_admin: str
    ):
        otro = await _crear_usuario(db_session, "Luis Pérez", "luis@ejemplo.com")
        await _cambiar_estado(client, token_admin, otro.id, False)

        r = await _cambiar_estado(client, token_admin, otro.id, True)

        assert r.status_code == 200
        assert r.json()["is_active"] is True
        login = await client.post(
            "/api/auth/login", json={"email": "luis@ejemplo.com", "password": "OtraPass123"}
        )
        assert login.status_code == 200

    async def test_el_administrador_no_puede_desactivarse_a_si_mismo(
        self, client: AsyncClient, admin: User, token_admin: str
    ):
        r = await _cambiar_estado(client, token_admin, admin.id, False)

        assert r.status_code == 400
        assert r.json()["detail"] == "No puedes desactivar tu propia cuenta."
        assert admin.is_active is True

    async def test_usuario_inexistente_devuelve_404(self, client: AsyncClient, token_admin: str):
        r = await _cambiar_estado(client, token_admin, 9999, False)
        assert r.status_code == 404

    async def test_exige_el_campo_activo(
        self, client: AsyncClient, db_session: AsyncSession, token_admin: str
    ):
        otro = await _crear_usuario(db_session, "Luis Pérez", "luis@ejemplo.com")
        r = await client.patch(
            f"/api/admin/usuarios/{otro.id}/estado", json={}, headers=_auth(token_admin)
        )
        assert r.status_code == 422
