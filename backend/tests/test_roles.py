"""Tests de roles de usuario y de las columnas nuevas de users."""

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.exceptions import UsuarioNoEncontradoError
from app.core.security import create_access_token, decode_access_token
from app.database import get_db
from app.models.user import ROL_ADMINISTRADOR, ROL_USUARIO, User
from app.services.auth_service import promover_a_administrador


USUARIO_BASE = {
    "nombre": "Ana García",
    "email": "ana@ejemplo.com",
    "password": "Segura123",
    "acepta_aviso": True,
}


async def _usuario_por_email(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

class TestRegistroConRol:
    async def test_registro_asigna_rol_usuario_y_fecha_de_aceptacion(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        assert r.status_code == 201

        user = await _usuario_por_email(db_session, USUARIO_BASE["email"])
        assert user.role == ROL_USUARIO
        assert user.privacy_accepted_at is not None
        assert user.sessions_valid_from is None

    async def test_registro_ignora_un_rol_enviado_por_el_cliente(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        r = await client.post(
            "/api/auth/register", json={**USUARIO_BASE, "role": ROL_ADMINISTRADOR}
        )
        assert r.status_code == 201

        user = await _usuario_por_email(db_session, USUARIO_BASE["email"])
        assert user.role == ROL_USUARIO


# ---------------------------------------------------------------------------
# Rol en el token y en el perfil
# ---------------------------------------------------------------------------

class TestRolEnTokenYPerfil:
    async def test_token_de_registro_incluye_el_rol(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        payload = decode_access_token(r.json()["access_token"])
        assert payload["role"] == ROL_USUARIO

    async def test_token_de_login_incluye_el_rol_vigente(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        await client.post("/api/auth/register", json=USUARIO_BASE)
        user = await _usuario_por_email(db_session, USUARIO_BASE["email"])
        user.role = ROL_ADMINISTRADOR
        await db_session.flush()

        r = await client.post(
            "/api/auth/login",
            json={"email": USUARIO_BASE["email"], "password": USUARIO_BASE["password"]},
        )
        assert decode_access_token(r.json()["access_token"])["role"] == ROL_ADMINISTRADOR

    async def test_me_devuelve_el_rol(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        token = r.json()["access_token"]
        me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["role"] == ROL_USUARIO


# ---------------------------------------------------------------------------
# Restricción de rutas al rol administrador
# ---------------------------------------------------------------------------

@pytest.fixture
async def cliente_con_ruta_admin(db_session: AsyncSession):
    """App mínima con una ruta protegida por require_admin: aún no hay rutas
    administrativas reales, así que la dependencia se prueba de forma aislada."""
    app_prueba = FastAPI()

    @app_prueba.get("/solo-admin")
    async def solo_admin(admin: User = Depends(require_admin)):
        return {"id": admin.id}

    async def override_get_db():
        yield db_session

    app_prueba.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app_prueba), base_url="http://test") as ac:
        yield ac


class TestRutasDeAdministrador:
    async def test_usuario_comun_recibe_403(self, cliente_con_ruta_admin, seed_user):
        token = create_access_token(str(seed_user.id))
        r = await cliente_con_ruta_admin.get(
            "/solo-admin", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 403

    async def test_administrador_accede(self, cliente_con_ruta_admin, db_session, seed_user):
        seed_user.role = ROL_ADMINISTRADOR
        await db_session.flush()
        token = create_access_token(str(seed_user.id), ROL_ADMINISTRADOR)

        r = await cliente_con_ruta_admin.get(
            "/solo-admin", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        assert r.json() == {"id": seed_user.id}

    async def test_rol_del_token_no_basta_sin_rol_en_la_base(
        self, cliente_con_ruta_admin, seed_user
    ):
        token = create_access_token(str(seed_user.id), ROL_ADMINISTRADOR)
        r = await cliente_con_ruta_admin.get(
            "/solo-admin", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 403

    async def test_sin_token_se_rechaza(self, cliente_con_ruta_admin):
        r = await cliente_con_ruta_admin.get("/solo-admin")
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Promoción a administrador (fuera de la API)
# ---------------------------------------------------------------------------

class TestPromoverAdministrador:
    async def test_promueve_a_un_usuario_existente(self, db_session, seed_user):
        user = await promover_a_administrador(db_session, seed_user.email)
        assert user.id == seed_user.id
        assert user.role == ROL_ADMINISTRADOR

    async def test_correo_inexistente_lanza_error(self, db_session):
        with pytest.raises(UsuarioNoEncontradoError):
            await promover_a_administrador(db_session, "nadie@privapp.test")
