"""Tests de roles de usuario y de las columnas nuevas de users."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import ROL_USUARIO, User


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
