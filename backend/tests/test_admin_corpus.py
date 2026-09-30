"""Tests de la administración del corpus normativo (rutas /api/admin/corpus).

El SQL del repositorio se prueba contra PostgreSQL en tests/integracion;
aquí se simula el repositorio para probar autorización, validación y respuesta.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import ROL_ADMINISTRADOR, User

REPO = "app.services.corpus_service.RepositorioCorpusNormativo"

DOCUMENTOS = [
    {
        "documento_fuente": "RGPD.pdf",
        "jurisdiccion": "internacional",
        "fragmentos": 120,
        "fecha_carga": datetime(2026, 5, 18, tzinfo=timezone.utc),
        "activo": True,
    },
    {
        "documento_fuente": "Decreto 57-2008.pdf",
        "jurisdiccion": "guatemala",
        "fragmentos": 40,
        "fecha_carga": datetime(2026, 5, 18, tzinfo=timezone.utc),
        "activo": False,
    },
]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def token_admin(db_session: AsyncSession, seed_user: User) -> str:
    seed_user.role = ROL_ADMINISTRADOR
    await db_session.flush()
    return create_access_token(str(seed_user.id), ROL_ADMINISTRADOR)


class TestListadoDelCorpus:
    async def test_usuario_comun_recibe_403(self, client: AsyncClient, seed_user: User):
        r = await client.get("/api/admin/corpus", headers=_auth(create_access_token(str(seed_user.id))))
        assert r.status_code == 403

    async def test_lista_los_documentos_con_su_resumen(self, client: AsyncClient, token_admin: str):
        with patch(f"{REPO}.listar_documentos", AsyncMock(return_value=DOCUMENTOS)):
            r = await client.get("/api/admin/corpus", headers=_auth(token_admin))

        assert r.status_code == 200
        documentos = r.json()["documentos"]
        assert [d["documento_fuente"] for d in documentos] == ["RGPD.pdf", "Decreto 57-2008.pdf"]
        assert documentos[0] == {
            "documento_fuente": "RGPD.pdf",
            "jurisdiccion": "internacional",
            "fragmentos": 120,
            "fecha_carga": "2026-05-18T00:00:00Z",
            "activo": True,
        }
        assert documentos[1]["activo"] is False

    async def test_corpus_vacio(self, client: AsyncClient, token_admin: str):
        with patch(f"{REPO}.listar_documentos", AsyncMock(return_value=[])):
            r = await client.get("/api/admin/corpus", headers=_auth(token_admin))
        assert r.json() == {"documentos": []}
