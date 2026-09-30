"""Tests de la aceptación obligatoria del aviso de privacidad al registrarse."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AvisoNoAceptadoError
from app.models.user import User
from app.services.auth_service import register_user


USUARIO_BASE = {
    "nombre": "Ana García",
    "email": "ana@ejemplo.com",
    "password": "Segura123",
    "acepta_aviso": True,
}


async def _contar_usuarios_con_email(db: AsyncSession, email: str) -> int:
    result = await db.execute(select(func.count()).select_from(User).where(User.email == email))
    return result.scalar_one()


class TestAceptacionDelAviso:
    async def test_registro_sin_aceptar_el_aviso_se_rechaza(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        r = await client.post("/api/auth/register", json={**USUARIO_BASE, "acepta_aviso": False})

        assert r.status_code == 422
        assert "aviso de privacidad" in r.text
        assert await _contar_usuarios_con_email(db_session, USUARIO_BASE["email"]) == 0

    async def test_registro_sin_el_campo_de_aceptacion_se_rechaza(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        sin_campo = {k: v for k, v in USUARIO_BASE.items() if k != "acepta_aviso"}
        r = await client.post("/api/auth/register", json=sin_campo)

        assert r.status_code == 422
        assert await _contar_usuarios_con_email(db_session, USUARIO_BASE["email"]) == 0

    async def test_registro_con_aceptacion_guarda_la_fecha(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        antes = datetime.now(timezone.utc)
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        assert r.status_code == 201

        result = await db_session.execute(select(User).where(User.email == USUARIO_BASE["email"]))
        user = result.scalar_one()
        # SQLite (pruebas) devuelve la fecha sin zona; se guarda en UTC.
        aceptado = user.privacy_accepted_at.replace(tzinfo=timezone.utc)
        assert aceptado >= antes

    async def test_el_servicio_no_registra_sin_aceptacion(self, db_session: AsyncSession):
        with pytest.raises(AvisoNoAceptadoError):
            await register_user(db_session, "Ana", "ana@ejemplo.com", "Segura123", False)
        assert await _contar_usuarios_con_email(db_session, "ana@ejemplo.com") == 0
