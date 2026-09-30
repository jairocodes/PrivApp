"""Tests de roles de usuario y de las columnas nuevas de users."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.models.user import ROL_ADMINISTRADOR, ROL_USUARIO, User


USUARIO_BASE = {
    "nombre": "Ana García",
    "email": "ana@ejemplo.com",
    "password": "Segura123",
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
