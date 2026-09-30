"""Tests del cambio de contraseña (POST /api/auth/change-password)."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, verify_password
from app.models.user import User

PASSWORD_ACTUAL = "TestPass123"  # la del usuario de conftest.seed_user


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _cuerpo(actual=PASSWORD_ACTUAL, nueva="NuevaClave456", confirmacion=None) -> dict:
    return {
        "password_actual": actual,
        "password_nueva": nueva,
        "confirmar_password": nueva if confirmacion is None else confirmacion,
    }


class TestCambioDePassword:
    async def test_cambio_exitoso_guarda_la_nueva_contrasena(
        self, client: AsyncClient, seed_user: User
    ):
        token = create_access_token(str(seed_user.id))

        r = await client.post("/api/auth/change-password", json=_cuerpo(), headers=_auth(token))

        assert r.status_code == 200
        assert verify_password("NuevaClave456", seed_user.hashed_password)
        assert not verify_password(PASSWORD_ACTUAL, seed_user.hashed_password)
        assert seed_user.sessions_valid_from is not None

    async def test_el_token_anterior_se_rechaza_y_el_nuevo_se_acepta(
        self, client: AsyncClient, seed_user: User
    ):
        token_anterior = create_access_token(str(seed_user.id))

        r = await client.post("/api/auth/change-password", json=_cuerpo(), headers=_auth(token_anterior))
        token_nuevo = r.json()["access_token"]

        assert (await client.get("/api/auth/me", headers=_auth(token_anterior))).status_code == 401
        assert (await client.get("/api/auth/me", headers=_auth(token_nuevo))).status_code == 200

    async def test_se_cierran_las_demas_sesiones_del_usuario(
        self, client: AsyncClient, seed_user: User
    ):
        otra_sesion = create_access_token(str(seed_user.id))
        esta_sesion = create_access_token(str(seed_user.id))

        await client.post("/api/auth/change-password", json=_cuerpo(), headers=_auth(esta_sesion))

        assert (await client.get("/api/analisis", headers=_auth(otra_sesion))).status_code == 401

    async def test_contrasena_actual_incorrecta(self, client: AsyncClient, seed_user: User):
        hash_original = seed_user.hashed_password
        token = create_access_token(str(seed_user.id))

        r = await client.post(
            "/api/auth/change-password", json=_cuerpo(actual="Incorrecta999"), headers=_auth(token)
        )

        assert r.status_code == 400
        assert r.json()["detail"] == "La contraseña actual es incorrecta."
        assert seed_user.hashed_password == hash_original
        assert seed_user.sessions_valid_from is None
        assert (await client.get("/api/auth/me", headers=_auth(token))).status_code == 200

    @pytest.mark.parametrize("debil", ["Corta1", "sinmayuscula123", "SinNumeros"])
    async def test_nueva_contrasena_debil(self, client: AsyncClient, seed_user: User, debil: str):
        token = create_access_token(str(seed_user.id))
        r = await client.post("/api/auth/change-password", json=_cuerpo(nueva=debil), headers=_auth(token))

        assert r.status_code == 422
        assert verify_password(PASSWORD_ACTUAL, seed_user.hashed_password)

    async def test_nueva_igual_a_la_actual(self, client: AsyncClient, seed_user: User):
        token = create_access_token(str(seed_user.id))
        r = await client.post(
            "/api/auth/change-password", json=_cuerpo(nueva=PASSWORD_ACTUAL), headers=_auth(token)
        )

        assert r.status_code == 400
        assert r.json()["detail"] == "La nueva contraseña debe ser distinta de la actual."
        assert seed_user.sessions_valid_from is None

    async def test_confirmacion_distinta(self, client: AsyncClient, seed_user: User):
        token = create_access_token(str(seed_user.id))
        r = await client.post(
            "/api/auth/change-password",
            json=_cuerpo(confirmacion="OtraClave789"),
            headers=_auth(token),
        )

        assert r.status_code == 422
        assert "confirmación" in r.text
        assert verify_password(PASSWORD_ACTUAL, seed_user.hashed_password)

    async def test_requiere_sesion(self, client: AsyncClient):
        r = await client.post("/api/auth/change-password", json=_cuerpo())
        assert r.status_code == 403
