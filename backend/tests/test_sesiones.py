"""Tests de la invalidación de todas las sesiones de un usuario."""

import time
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, decode_access_token
from app.models.user import User


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _token_sin_iat(user_id: int) -> str:
    """Token con el formato anterior (sin fecha de emisión)."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "jti": "token-sin-iat",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def _invalidar_sesiones(db: AsyncSession, user: User) -> None:
    user.sessions_valid_from = datetime.now(timezone.utc)
    await db.flush()


# ---------------------------------------------------------------------------
# Fecha de emisión del token
# ---------------------------------------------------------------------------

class TestFechaDeEmision:
    def test_token_incluye_iat_con_fraccion_de_segundo(self):
        antes = time.time()
        payload = decode_access_token(create_access_token("1"))
        despues = time.time()

        assert antes <= payload["iat"] <= despues
        assert isinstance(payload["iat"], float)


# ---------------------------------------------------------------------------
# Rechazo de tokens anteriores a sessions_valid_from
# ---------------------------------------------------------------------------

class TestInvalidacionDeSesiones:
    async def test_token_emitido_antes_de_la_invalidacion_se_rechaza(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        token_anterior = create_access_token(str(seed_user.id))
        await _invalidar_sesiones(db_session, seed_user)

        r = await client.get("/api/auth/me", headers=_auth(token_anterior))
        assert r.status_code == 401

    async def test_token_emitido_despues_de_la_invalidacion_se_acepta(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        await _invalidar_sesiones(db_session, seed_user)
        token_nuevo = create_access_token(str(seed_user.id))

        r = await client.get("/api/auth/me", headers=_auth(token_nuevo))
        assert r.status_code == 200

    async def test_la_invalidacion_afecta_a_todas_las_sesiones_del_usuario(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        sesiones = [create_access_token(str(seed_user.id)) for _ in range(3)]
        await _invalidar_sesiones(db_session, seed_user)

        for token in sesiones:
            r = await client.get("/api/analisis", headers=_auth(token))
            assert r.status_code == 401

    async def test_sin_invalidacion_los_tokens_sin_iat_siguen_aceptandose(
        self, client: AsyncClient, seed_user: User
    ):
        r = await client.get("/api/auth/me", headers=_auth(_token_sin_iat(seed_user.id)))
        assert r.status_code == 200

    async def test_tras_la_invalidacion_un_token_sin_iat_se_rechaza(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        token = _token_sin_iat(seed_user.id)
        await _invalidar_sesiones(db_session, seed_user)

        r = await client.get("/api/auth/me", headers=_auth(token))
        assert r.status_code == 401

    async def test_la_revocacion_en_redis_sigue_funcionando(
        self, client: AsyncClient, db_session: AsyncSession, seed_user: User
    ):
        await _invalidar_sesiones(db_session, seed_user)
        token = create_access_token(str(seed_user.id))

        logout = await client.post("/api/auth/logout", headers=_auth(token))
        assert logout.status_code == 200

        r = await client.get("/api/auth/me", headers=_auth(token))
        assert r.status_code == 401
