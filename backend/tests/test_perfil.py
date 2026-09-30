"""Tests de la edición del perfil (PATCH /api/auth/me)."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


class TestEdicionDePerfil:
    async def test_actualiza_el_nombre(self, client: AsyncClient, seed_user: User):
        r = await client.patch("/api/auth/me", json={"nombre": "Ana María"}, headers=_auth(seed_user))

        assert r.status_code == 200
        assert r.json()["nombre"] == "Ana María"
        me = await client.get("/api/auth/me", headers=_auth(seed_user))
        assert me.json()["nombre"] == "Ana María"

    async def test_quita_los_espacios_de_los_extremos(self, client: AsyncClient, seed_user: User):
        r = await client.patch("/api/auth/me", json={"nombre": "  Ana María  "}, headers=_auth(seed_user))
        assert r.json()["nombre"] == "Ana María"

    async def test_el_correo_no_se_modifica(self, client: AsyncClient, seed_user: User):
        correo_original = seed_user.email
        r = await client.patch(
            "/api/auth/me",
            json={"nombre": "Ana María", "email": "otro@ejemplo.com"},
            headers=_auth(seed_user),
        )

        assert r.status_code == 200
        assert r.json()["email"] == correo_original
        assert seed_user.email == correo_original

    @pytest.mark.parametrize("nombre", ["", "   ", "A", "x" * 101])
    async def test_rechaza_nombres_vacios_cortos_o_demasiado_largos(
        self, client: AsyncClient, seed_user: User, nombre: str
    ):
        nombre_original = seed_user.nombre
        r = await client.patch("/api/auth/me", json={"nombre": nombre}, headers=_auth(seed_user))

        assert r.status_code == 422
        assert seed_user.nombre == nombre_original

    async def test_acepta_el_maximo_de_100_caracteres(self, client: AsyncClient, seed_user: User):
        r = await client.patch("/api/auth/me", json={"nombre": "x" * 100}, headers=_auth(seed_user))
        assert r.status_code == 200

    async def test_requiere_sesion(self, client: AsyncClient):
        r = await client.patch("/api/auth/me", json={"nombre": "Ana María"})
        assert r.status_code == 403
