"""Tests de la eliminación de la propia cuenta (DELETE /api/auth/me)."""

from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.security import create_access_token, hash_password
from app.models.analysis import AnalysisTemp
from app.models.user import ROL_ADMINISTRADOR, User

PASSWORD = "TestPass123"  # la del usuario de conftest.seed_user


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _eliminar(client: AsyncClient, token: str, password: str = PASSWORD):
    return await client.request("DELETE", "/api/auth/me", json={"password": password}, headers=_auth(token))


async def _agregar_analisis(db_session, user_id: int, estado: str = "completado") -> None:
    db_session.add(AnalysisTemp(user_id=user_id, texto_original="t", estado=estado))
    await db_session.flush()


async def _contar(db_session, modelo, *condiciones) -> int:
    return await db_session.scalar(select(func.count()).select_from(modelo).where(*condiciones))


async def _otro_usuario(db_session, email="otra@ejemplo.com", role="usuario") -> User:
    user = User(
        nombre="Otra persona", email=email, hashed_password=hash_password(PASSWORD),
        is_active=True, role=role, privacy_accepted_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    return user


class TestEliminarCuenta:
    async def test_elimina_la_cuenta_y_todos_sus_analisis(self, client, db_session, seed_user):
        otra = await _otro_usuario(db_session)
        await _agregar_analisis(db_session, seed_user.id)
        await _agregar_analisis(db_session, seed_user.id)
        await _agregar_analisis(db_session, otra.id)
        user_id = seed_user.id

        r = await _eliminar(client, create_access_token(str(user_id)))

        assert r.status_code == 204
        assert await _contar(db_session, User, User.id == user_id) == 0
        assert await _contar(db_session, AnalysisTemp, AnalysisTemp.user_id == user_id) == 0
        # Los datos de las demás personas no se tocan.
        assert await _contar(db_session, AnalysisTemp, AnalysisTemp.user_id == otra.id) == 1

    async def test_ningun_token_de_la_cuenta_sigue_sirviendo(self, client, seed_user):
        esta_sesion = create_access_token(str(seed_user.id))
        otra_sesion = create_access_token(str(seed_user.id))

        await _eliminar(client, esta_sesion)

        assert (await client.get("/api/auth/me", headers=_auth(esta_sesion))).status_code == 401
        assert (await client.get("/api/analisis", headers=_auth(otra_sesion))).status_code == 401

    async def test_el_correo_queda_libre_para_registrarse_de_nuevo(self, client, db_session):
        otra = await _otro_usuario(db_session)
        await _eliminar(client, create_access_token(str(otra.id)))

        login = await client.post("/api/auth/login", json={"email": otra.email, "password": PASSWORD})
        registro = await client.post("/api/auth/register", json={
            "nombre": "Otra persona", "email": otra.email, "password": PASSWORD, "acepta_aviso": True,
        })
        assert login.status_code == 401
        assert registro.status_code == 201

    async def test_contrasena_incorrecta_no_elimina_nada(self, client, db_session, seed_user):
        await _agregar_analisis(db_session, seed_user.id)

        r = await _eliminar(client, create_access_token(str(seed_user.id)), password="Otra1234")

        assert r.status_code == 400
        assert r.json()["detail"] == "La contraseña es incorrecta."
        assert await _contar(db_session, AnalysisTemp, AnalysisTemp.user_id == seed_user.id) == 1

    async def test_sin_contrasena_retorna_422(self, client, seed_user):
        r = await client.request(
            "DELETE", "/api/auth/me", json={}, headers=_auth(create_access_token(str(seed_user.id)))
        )
        assert r.status_code == 422

    async def test_sin_autenticacion_retorna_403(self, client):
        r = await client.request("DELETE", "/api/auth/me", json={"password": PASSWORD})
        assert r.status_code == 403

    async def test_con_un_analisis_en_curso_retorna_409(self, client, db_session, seed_user):
        await _agregar_analisis(db_session, seed_user.id, estado="procesando")

        r = await _eliminar(client, create_access_token(str(seed_user.id)))

        assert r.status_code == 409
        assert "análisis en curso" in r.json()["detail"]
        assert await _contar(db_session, User, User.id == seed_user.id) == 1

    async def test_el_unico_administrador_no_puede_eliminarse(self, client, db_session, seed_user):
        seed_user.role = ROL_ADMINISTRADOR
        await db_session.flush()

        r = await _eliminar(client, create_access_token(str(seed_user.id), ROL_ADMINISTRADOR))

        assert r.status_code == 400
        assert "único administrador" in r.json()["detail"]

    async def test_un_administrador_puede_eliminarse_si_hay_otro(self, client, db_session, seed_user):
        seed_user.role = ROL_ADMINISTRADOR
        await _otro_usuario(db_session, email="admin2@ejemplo.com", role=ROL_ADMINISTRADOR)

        r = await _eliminar(client, create_access_token(str(seed_user.id), ROL_ADMINISTRADOR))

        assert r.status_code == 204
