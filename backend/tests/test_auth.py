"""Tests del módulo de autenticación."""

import pytest
from httpx import AsyncClient


USUARIO_BASE = {
    "nombre": "Ana García",
    "email": "ana@ejemplo.com",
    "password": "Segura123",
}


# ---------------------------------------------------------------------------
# Sistema
# ---------------------------------------------------------------------------

class TestHealthcheck:
    async def test_healthcheck_ok(self, client: AsyncClient):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

class TestRegistro:
    async def test_registro_exitoso(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_registro_devuelve_token_valido(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        token = r.json()["access_token"]
        me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == USUARIO_BASE["email"]

    async def test_registro_email_duplicado(self, client: AsyncClient):
        await client.post("/api/auth/register", json=USUARIO_BASE)
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        assert r.status_code == 409

    async def test_registro_email_invalido(self, client: AsyncClient):
        payload = {**USUARIO_BASE, "email": "no-es-un-email"}
        r = await client.post("/api/auth/register", json=payload)
        assert r.status_code == 422

    async def test_registro_password_sin_mayuscula(self, client: AsyncClient):
        payload = {**USUARIO_BASE, "email": "b@b.com", "password": "sinmayus123"}
        r = await client.post("/api/auth/register", json=payload)
        assert r.status_code == 422

    async def test_registro_password_sin_numero(self, client: AsyncClient):
        payload = {**USUARIO_BASE, "email": "c@c.com", "password": "SinNumero"}
        r = await client.post("/api/auth/register", json=payload)
        assert r.status_code == 422

    async def test_registro_password_muy_corta(self, client: AsyncClient):
        payload = {**USUARIO_BASE, "email": "d@d.com", "password": "Cor1"}
        r = await client.post("/api/auth/register", json=payload)
        assert r.status_code == 422

    async def test_registro_nombre_muy_corto(self, client: AsyncClient):
        payload = {**USUARIO_BASE, "nombre": "A"}
        r = await client.post("/api/auth/register", json=payload)
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    async def test_login_exitoso(self, client: AsyncClient):
        await client.post("/api/auth/register", json=USUARIO_BASE)
        r = await client.post(
            "/api/auth/login",
            json={"email": USUARIO_BASE["email"], "password": USUARIO_BASE["password"]},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_login_password_incorrecta(self, client: AsyncClient):
        await client.post("/api/auth/register", json=USUARIO_BASE)
        r = await client.post(
            "/api/auth/login",
            json={"email": USUARIO_BASE["email"], "password": "Incorrecta99"},
        )
        assert r.status_code == 401

    async def test_login_usuario_inexistente(self, client: AsyncClient):
        r = await client.post(
            "/api/auth/login",
            json={"email": "noexiste@x.com", "password": "Cualquiera1"},
        )
        assert r.status_code == 401

    async def test_login_email_invalido(self, client: AsyncClient):
        r = await client.post(
            "/api/auth/login",
            json={"email": "no-es-email", "password": "Algo123"},
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Rutas protegidas
# ---------------------------------------------------------------------------

class TestRutasProtegidas:
    async def test_me_sin_token_devuelve_403(self, client: AsyncClient):
        r = await client.get("/api/auth/me")
        assert r.status_code == 403

    async def test_me_con_token_invalido(self, client: AsyncClient):
        r = await client.get("/api/auth/me", headers={"Authorization": "Bearer token_falso"})
        assert r.status_code == 401

    async def test_me_con_token_valido(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        token = r.json()["access_token"]
        me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        data = me.json()
        assert data["email"] == USUARIO_BASE["email"]
        assert data["nombre"] == USUARIO_BASE["nombre"]
        assert "id" in data

    async def test_logout_exitoso(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json=USUARIO_BASE)
        token = r.json()["access_token"]
        logout = await client.post(
            "/api/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )
        assert logout.status_code == 200

    async def test_logout_sin_token_devuelve_403(self, client: AsyncClient):
        r = await client.post("/api/auth/logout")
        assert r.status_code == 403
