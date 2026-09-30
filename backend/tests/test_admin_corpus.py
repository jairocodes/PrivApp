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
from tests.pdf_de_prueba import LINEAS_POLITICA, pdf_con_texto, pdf_sin_texto
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


class TestCambioDeEstadoDelDocumento:
    async def test_usuario_comun_recibe_403(self, client: AsyncClient, seed_user: User):
        r = await client.patch(
            "/api/admin/corpus/estado",
            json={"documento_fuente": "RGPD.pdf", "activo": False},
            headers=_auth(create_access_token(str(seed_user.id))),
        )
        assert r.status_code == 403

    async def test_desactiva_el_documento_completo(self, client: AsyncClient, token_admin: str):
        cambiar = AsyncMock(return_value=120)
        desactivado = {**DOCUMENTOS[0], "activo": False}
        with patch(f"{REPO}.cambiar_estado_documento", cambiar), \
             patch(f"{REPO}.obtener_documento", AsyncMock(return_value=desactivado)):
            r = await client.patch(
                "/api/admin/corpus/estado",
                json={"documento_fuente": "RGPD.pdf", "activo": False},
                headers=_auth(token_admin),
            )

        assert r.status_code == 200
        assert r.json()["activo"] is False
        cambiar.assert_awaited_once_with("RGPD.pdf", False)

    async def test_documento_inexistente_devuelve_404(self, client: AsyncClient, token_admin: str):
        with patch(f"{REPO}.cambiar_estado_documento", AsyncMock(return_value=0)):
            r = await client.patch(
                "/api/admin/corpus/estado",
                json={"documento_fuente": "no-existe.pdf", "activo": True},
                headers=_auth(token_admin),
            )
        assert r.status_code == 404

    async def test_exige_el_documento_y_el_estado(self, client: AsyncClient, token_admin: str):
        r = await client.patch("/api/admin/corpus/estado", json={"activo": True}, headers=_auth(token_admin))
        assert r.status_code == 422


SERVICIO = "app.services.corpus_service"
TEXTO_NORMA = " ".join(LINEAS_POLITICA * 3)


async def _cargar(client, token, nombre="Norma nueva.pdf", contenido=None, tipo="application/pdf",
                  jurisdiccion="internacional"):
    return await client.post(
        "/api/admin/corpus",
        files={"archivo": (nombre, pdf_con_texto(LINEAS_POLITICA * 3) if contenido is None else contenido, tipo)},
        data={"jurisdiccion": jurisdiccion},
        headers=_auth(token),
    )


class TestCargaDeDocumentos:
    async def test_usuario_comun_recibe_403(self, client: AsyncClient, seed_user: User):
        r = await _cargar(client, create_access_token(str(seed_user.id)))
        assert r.status_code == 403

    async def test_carga_un_pdf_y_lo_deja_activo(self, client: AsyncClient, token_admin: str):
        insertar = AsyncMock(return_value=(6, 0))
        resumen = {**DOCUMENTOS[0], "documento_fuente": "Norma nueva.pdf", "fragmentos": 6}
        with patch(f"{REPO}.obtener_documento", AsyncMock(side_effect=[None, resumen])), \
             patch(f"{SERVICIO}.insertar_fragmentos", insertar):
            r = await _cargar(client, token_admin)

        assert r.status_code == 201
        datos = r.json()
        assert datos["documento_fuente"] == "Norma nueva.pdf"
        assert datos["activo"] is True
        assert datos["fragmentos_insertados"] == 6
        _, nombre, texto, jurisdiccion, extra = insertar.await_args.args
        assert (nombre, jurisdiccion) == ("Norma nueva.pdf", "internacional")
        assert "Recopilamos su nombre" in texto
        assert extra == {"origen": "carga_administrador"}

    async def test_carga_un_txt(self, client: AsyncClient, token_admin: str):
        resumen = {**DOCUMENTOS[0], "documento_fuente": "norma.txt"}
        with patch(f"{REPO}.obtener_documento", AsyncMock(side_effect=[None, resumen])), \
             patch(f"{SERVICIO}.insertar_fragmentos", AsyncMock(return_value=(3, 0))):
            r = await _cargar(client, token_admin, "norma.txt", TEXTO_NORMA.encode(), "text/plain")
        assert r.status_code == 201

    async def test_rechaza_una_jurisdiccion_desconocida(self, client: AsyncClient, token_admin: str):
        r = await _cargar(client, token_admin, jurisdiccion="mexico")
        assert r.status_code == 422

    async def test_rechaza_extensiones_no_permitidas(self, client: AsyncClient, token_admin: str):
        r = await _cargar(client, token_admin, "norma.docx", b"x", "application/octet-stream")
        assert r.status_code == 415

    async def test_rechaza_archivos_de_mas_de_5_mb(self, client: AsyncClient, token_admin: str):
        r = await _cargar(client, token_admin, "norma.txt", b"a " * (3 * 1024 * 1024), "text/plain")
        assert r.status_code == 413

    async def test_rechaza_un_pdf_sin_texto_suficiente(self, client: AsyncClient, token_admin: str):
        r = await _cargar(client, token_admin, "escaneado.pdf", pdf_sin_texto())
        assert r.status_code == 422
        assert "mínimo 50 palabras" in r.json()["detail"]

    async def test_rechaza_un_documento_con_nombre_existente(self, client: AsyncClient, token_admin: str):
        insertar = AsyncMock()
        with patch(f"{REPO}.obtener_documento", AsyncMock(return_value=DOCUMENTOS[0])), \
             patch(f"{SERVICIO}.insertar_fragmentos", insertar):
            r = await _cargar(client, token_admin, "RGPD.pdf")

        assert r.status_code == 409
        insertar.assert_not_awaited()

    async def test_quita_la_ruta_del_nombre_del_archivo(self, client: AsyncClient, token_admin: str):
        insertar = AsyncMock(return_value=(6, 0))
        resumen = {**DOCUMENTOS[0], "documento_fuente": "norma.pdf"}
        with patch(f"{REPO}.obtener_documento", AsyncMock(side_effect=[None, resumen])), \
             patch(f"{SERVICIO}.insertar_fragmentos", insertar):
            await _cargar(client, token_admin, "C:\\docs\\norma.pdf")

        assert insertar.await_args.args[1] == "norma.pdf"


class TestProteccionDeLaCarga:
    async def test_un_envio_enorme_se_rechaza_antes_de_leerlo(self, client: AsyncClient, token_admin: str):
        r = await client.post(
            "/api/admin/corpus",
            content=b"x" * (6 * 1024 * 1024 + 1),
            headers={**_auth(token_admin), "Content-Type": "multipart/form-data; boundary=limite"},
        )
        assert r.status_code == 413
        assert r.json()["detail"] == "El archivo supera el tamaño máximo de 5 MB."

    async def test_el_listado_del_corpus_no_se_ve_afectado(self, client: AsyncClient, token_admin: str):
        # El rechazo temprano solo aplica a POST: GET /api/admin/corpus sigue igual.
        with patch(f"{REPO}.listar_documentos", AsyncMock(return_value=[])):
            r = await client.get("/api/admin/corpus", headers={**_auth(token_admin), "Content-Length": str(10**9)})
        assert r.status_code == 200

    async def test_limita_las_cargas_por_minuto(self, client: AsyncClient, token_admin: str):
        codigos = []
        for _ in range(6):
            r = await _cargar(client, token_admin, "norma.docx", b"x", "application/octet-stream")
            codigos.append(r.status_code)
        assert codigos == [415] * 5 + [429]

