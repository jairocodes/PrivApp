"""Tests de la aceptación obligatoria del aviso de privacidad al registrarse."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AvisoNoAceptadoError, DeclaracionEdadFaltanteError
from app.models.user import User
from app.services.auth_service import register_user


USUARIO_BASE = {
    "nombre": "Ana García",
    "email": "ana@ejemplo.com",
    "password": "Segura123",
    "acepta_aviso": True,
    "declara_edad": True,
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
            await register_user(db_session, "Ana", "ana@ejemplo.com", "Segura123", False, True)
        assert await _contar_usuarios_con_email(db_session, "ana@ejemplo.com") == 0


class TestDeclaracionDeEdad:
    """Mayoría de edad o consentimiento de la madre, el padre o la persona
    encargada (cláusula de menores del contrato de servicios de OpenAI)."""

    @pytest.mark.parametrize("cuerpo", [
        {**USUARIO_BASE, "declara_edad": False},
        {k: v for k, v in USUARIO_BASE.items() if k != "declara_edad"},
    ])
    async def test_registro_sin_la_declaracion_se_rechaza(
        self, client: AsyncClient, db_session: AsyncSession, cuerpo
    ):
        r = await client.post("/api/auth/register", json=cuerpo)

        assert r.status_code == 422
        assert await _contar_usuarios_con_email(db_session, USUARIO_BASE["email"]) == 0

    async def test_el_mensaje_explica_la_declaracion(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json={**USUARIO_BASE, "declara_edad": False})
        assert "mayor de 18 años" in r.text

    async def test_registro_con_la_declaracion_guarda_la_fecha(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        assert r.status_code == 201

        user = (await db_session.execute(select(User).where(User.email == USUARIO_BASE["email"]))).scalar_one()
        assert user.age_declaration_at is not None
        assert user.age_declaration_at == user.privacy_accepted_at

    async def test_el_servicio_no_registra_sin_la_declaracion(self, db_session: AsyncSession):
        with pytest.raises(DeclaracionEdadFaltanteError):
            await register_user(db_session, "Ana", "ana@ejemplo.com", "Segura123", True, False)
        assert await _contar_usuarios_con_email(db_session, "ana@ejemplo.com") == 0
