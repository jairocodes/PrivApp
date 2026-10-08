"""Tests de la carga de archivos PDF o TXT (POST /api/ingesta/archivo)."""

from starlette.formparsers import MultiPartParser

from app.core.security import create_access_token
from app.services.ingesta_service import TAMANO_MAXIMO_ARCHIVO
from tests.pdf_de_prueba import LINEAS_POLITICA, pdf_con_texto, pdf_sin_texto

TEXTO_POLITICA = " ".join(LINEAS_POLITICA)


def _auth() -> dict:
    return {"Authorization": f"Bearer {create_access_token('1')}"}


async def _subir(client, nombre: str, contenido: bytes, tipo: str, headers=None):
    return await client.post(
        "/api/ingesta/archivo",
        files={"archivo": (nombre, contenido, tipo)},
        headers=_auth() if headers is None else headers,
    )


class TestCargaDeArchivoValida:
    async def test_pdf_valido(self, client):
        r = await _subir(client, "politica.pdf", pdf_con_texto(LINEAS_POLITICA), "application/pdf")

        assert r.status_code == 200
        datos = r.json()
        assert "Recopilamos su nombre" in datos["texto_procesado"]
        assert datos["caracteres"] == len(datos["texto_procesado"])
        assert datos["palabras"] >= 40
        assert datos["fuente"] == "politica.pdf"

    async def test_txt_valido_en_utf8(self, client):
        texto = "Política de privacidad: recopilamos información básica. " + TEXTO_POLITICA
        r = await _subir(client, "politica.txt", texto.encode("utf-8"), "text/plain")

        assert r.status_code == 200
        assert r.json()["texto_procesado"].startswith("Política de privacidad: recopilamos información")

    async def test_txt_guardado_en_windows_1252(self, client):
        texto = "Política de privacidad y protección de datos. " + TEXTO_POLITICA
        r = await _subir(client, "politica.txt", texto.encode("cp1252"), "text/plain; charset=windows-1252")

        assert r.status_code == 200
        assert r.json()["texto_procesado"].startswith("Política de privacidad y protección")

    async def test_el_texto_se_normaliza(self, client):
        texto = "   " + "   \n\n\n\n".join(LINEAS_POLITICA) + "   "
        r = await _subir(client, "politica.txt", texto.encode("utf-8"), "text/plain")

        assert "\n\n\n" not in r.json()["texto_procesado"]
        assert not r.json()["texto_procesado"].startswith(" ")

    async def test_la_fuente_no_incluye_rutas_del_cliente(self, client):
        for nombre in ("C:\\carpeta\\politica.txt", "/home/ana/politica.txt"):
            r = await _subir(client, nombre, TEXTO_POLITICA.encode(), "text/plain")
            assert r.json()["fuente"] == "politica.txt"


class TestCargaDeArchivoRechazada:
    async def test_extension_no_permitida(self, client):
        r = await _subir(client, "politica.docx", b"contenido", "application/octet-stream")

        assert r.status_code == 415
        assert r.json()["detail"] == "Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt)."

    async def test_tipo_de_contenido_que_no_corresponde_a_la_extension(self, client):
        r = await _subir(client, "politica.pdf", pdf_con_texto(LINEAS_POLITICA), "text/plain")
        assert r.status_code == 415

    async def test_archivo_que_se_hace_pasar_por_pdf(self, client):
        r = await _subir(client, "politica.pdf", TEXTO_POLITICA.encode(), "application/pdf")
        assert r.status_code == 415

    async def test_archivo_de_mas_de_5_mb(self, client):
        contenido = b"a " * (TAMANO_MAXIMO_ARCHIVO // 2 + 1)
        assert len(contenido) > TAMANO_MAXIMO_ARCHIVO

        r = await _subir(client, "politica.txt", contenido, "text/plain")

        assert r.status_code == 413
        assert r.json()["detail"] == "El archivo supera el tamaño máximo de 5 MB."

    async def test_pdf_sin_texto_extraible(self, client):
        r = await _subir(client, "escaneado.pdf", pdf_sin_texto(), "application/pdf")

        assert r.status_code == 422
        assert "No se encontró texto en el PDF" in r.json()["detail"]

    async def test_aplica_la_regla_de_longitud(self, client):
        r = await _subir(client, "corta.pdf", pdf_con_texto(["Politica muy breve."]), "application/pdf")

        assert r.status_code == 422
        assert r.json()["detail"] == "El texto debe tener al menos 200 caracteres y 40 palabras."

    async def test_requiere_sesion(self, client):
        r = await _subir(client, "politica.txt", TEXTO_POLITICA.encode(), "text/plain", headers={})
        assert r.status_code == 403


def test_un_archivo_dentro_del_limite_se_procesa_en_memoria():
    # Starlette solo escribe en disco las partes que superan este umbral.
    assert MultiPartParser.max_file_size > TAMANO_MAXIMO_ARCHIVO


class TestRechazoTemprano:
    async def test_un_envio_mayor_al_limite_se_rechaza_por_su_content_length(self, client):
        cuerpo = b"x" * (6 * 1024 * 1024 + 1)
        r = await client.post(
            "/api/ingesta/archivo",
            content=cuerpo,
            headers={**_auth(), "Content-Type": "multipart/form-data; boundary=limite"},
        )

        assert r.status_code == 413
        assert r.json()["detail"] == "El archivo supera el tamaño máximo de 5 MB."

    async def test_el_rechazo_temprano_no_exige_leer_el_cuerpo(self):
        from app.core.limite_carga import LimiteCargaArchivoMiddleware

        async def app_interna(scope, receive, send):
            raise AssertionError("no debería llegar a la aplicación")

        async def receive():
            raise AssertionError("no debería leer el cuerpo")

        enviados = []

        async def send(mensaje):
            enviados.append(mensaje)

        middleware = LimiteCargaArchivoMiddleware(app_interna, max_bytes=10)
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/ingesta/archivo",
            "headers": [(b"content-length", b"11")],
        }
        await middleware(scope, receive, send)

        assert enviados[0]["status"] == 413

    async def test_no_afecta_a_otras_rutas(self, client):
        r = await client.post(
            "/api/ingesta/texto",
            json={"texto": TEXTO_POLITICA + " " * (6 * 1024 * 1024)},
            headers=_auth(),
        )
        assert r.status_code != 413

