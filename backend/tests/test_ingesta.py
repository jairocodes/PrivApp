"""Tests del módulo de ingesta de políticas de privacidad.

- TestLimpiezaTexto: pruebas unitarias de limpiar_texto (función pura)
- TestIngestaServicio: pruebas de procesar_texto_directo y extraer_texto_url con mocks
- TestEndpointsIngesta: pruebas de integración de los endpoints /api/ingesta/*
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ExtraccionURLError, TextoDemasiadoCortoError


# ---------------------------------------------------------------------------
# Limpieza de texto — función pura
# ---------------------------------------------------------------------------

class TestLimpiezaTexto:
    def test_colapsa_espacios_multiples(self):
        from app.services.ingesta_service import limpiar_texto

        resultado = limpiar_texto("Hola    mundo   privacidad")
        assert "    " not in resultado
        assert "Hola mundo privacidad" in resultado

    def test_colapsa_saltos_de_linea_excesivos(self):
        from app.services.ingesta_service import limpiar_texto

        texto = "Párrafo uno.\n\n\n\nPárrafo dos."
        resultado = limpiar_texto(texto)
        assert "\n\n\n" not in resultado

    def test_preserva_saltos_de_parrafo(self):
        from app.services.ingesta_service import limpiar_texto

        texto = "Párrafo uno.\n\nPárrafo dos."
        resultado = limpiar_texto(texto)
        assert "\n\n" in resultado

    def test_texto_vacio_devuelve_vacio(self):
        from app.services.ingesta_service import limpiar_texto

        assert limpiar_texto("") == ""
        assert limpiar_texto("   \n\n   ") == ""

    def test_normaliza_unicode(self):
        from app.services.ingesta_service import limpiar_texto

        # á puede ser NFC (U+00E1) o NFD (a + U+0301)
        nfd = "política"  # NFD: a + combining acute accent
        resultado = limpiar_texto(nfd)
        assert resultado == "política"  # NFC


# ---------------------------------------------------------------------------
# Servicio de ingesta — texto directo
# ---------------------------------------------------------------------------

class TestIngestaServicio:
    def test_texto_valido_retorna_limpio(self):
        from app.services.ingesta_service import procesar_texto_directo

        texto = (
            "La presente política de privacidad explica cómo recopilamos y usamos "
            "sus datos personales. "
        ) * 5
        resultado = procesar_texto_directo(texto)
        assert len(resultado) > 0

    def test_texto_muy_corto_lanza_excepcion(self):
        from app.services.ingesta_service import procesar_texto_directo

        with pytest.raises(TextoDemasiadoCortoError):
            procesar_texto_directo("Texto corto.")

    def test_texto_demasiado_largo_lanza_excepcion(self):
        from app.services.ingesta_service import MAX_CARACTERES, procesar_texto_directo

        texto_gigante = "palabra " * (MAX_CARACTERES // 7 + 1)
        with pytest.raises(Exception):
            procesar_texto_directo(texto_gigante)

    def test_extraccion_url_exito_contenido_suficiente(self):
        from app.services.ingesta_service import extraer_texto_url

        parrafo = (
            "Política de privacidad de nuestra empresa. "
            "Recopilamos datos para mejorar nuestros servicios. "
            "Los datos se almacenan de forma segura y no se comparten con terceros. "
        ) * 6  # ~120 palabras

        html_mock = f"<html><body><main><p>{parrafo}</p></main></body></html>"
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.text = html_mock
        response_mock.headers = {"content-type": "text/html; charset=utf-8"}
        response_mock.raise_for_status = MagicMock()

        with patch("app.services.ingesta_service.requests.get", return_value=response_mock):
            resultado = extraer_texto_url("https://ejemplo.com/privacidad")

        assert len(resultado.split()) >= 40

    def test_extraccion_url_timeout(self):
        import requests as req

        from app.services.ingesta_service import extraer_texto_url

        with patch(
            "app.services.ingesta_service.requests.get",
            side_effect=req.exceptions.Timeout,
        ):
            with pytest.raises(ExtraccionURLError) as exc_info:
                extraer_texto_url("https://ejemplo.com/privacidad")
        assert "tardó" in str(exc_info.value.detail).lower()

    def test_extraccion_url_error_conexion(self):
        import requests as req

        from app.services.ingesta_service import extraer_texto_url

        with patch(
            "app.services.ingesta_service.requests.get",
            side_effect=req.exceptions.ConnectionError,
        ):
            with pytest.raises(ExtraccionURLError) as exc_info:
                extraer_texto_url("https://ejemplo.com/privacidad")
        assert "conectar" in str(exc_info.value.detail).lower()

    def test_extraccion_url_contenido_no_html(self):
        from app.services.ingesta_service import extraer_texto_url

        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.headers = {"content-type": "application/pdf"}
        response_mock.raise_for_status = MagicMock()

        with patch("app.services.ingesta_service.requests.get", return_value=response_mock):
            with pytest.raises(ExtraccionURLError) as exc_info:
                extraer_texto_url("https://ejemplo.com/privacidad.pdf")
        assert "html" in str(exc_info.value.detail).lower()

    def test_extraccion_url_http_404(self):
        import requests as req

        from app.services.ingesta_service import extraer_texto_url

        http_error = req.exceptions.HTTPError()
        error_response = MagicMock()
        error_response.status_code = 404
        http_error.response = error_response

        with patch(
            "app.services.ingesta_service.requests.get",
            side_effect=http_error,
        ):
            with pytest.raises(ExtraccionURLError) as exc_info:
                extraer_texto_url("https://ejemplo.com/privacidad")
        assert "404" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# Endpoints de ingesta — integración con cliente HTTP
# ---------------------------------------------------------------------------

class TestEndpointsIngesta:
    async def test_ingesta_texto_sin_autenticacion_retorna_403(self, client):
        response = await client.post(
            "/api/ingesta/texto",
            json={"texto": "texto " * 50},
        )
        assert response.status_code == 403

    async def test_ingesta_url_sin_autenticacion_retorna_403(self, client):
        response = await client.post(
            "/api/ingesta/url",
            json={"url": "https://ejemplo.com/privacidad"},
        )
        assert response.status_code == 403

    async def test_ingesta_texto_autenticado_exitoso(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        texto_largo = (
            "Esta política de privacidad describe cómo nuestra organización recopila, "
            "utiliza y protege la información personal que usted proporciona al utilizar "
            "nuestros servicios en línea. Al acceder a nuestra plataforma, usted acepta "
            "los términos aquí descritos. "
        ) * 8

        with patch(
            "app.api.v1.ingesta.procesar_texto_directo",
            return_value=texto_largo,
        ):
            response = await client.post(
                "/api/ingesta/texto",
                json={"texto": texto_largo},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "texto_procesado" in data
        assert "palabras" in data
        assert data["fuente"] == "texto_directo"

    async def test_ingesta_texto_demasiado_corto_retorna_422(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        response = await client.post(
            "/api/ingesta/texto",
            json={"texto": "Texto muy corto."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_ingesta_url_autenticada_exitosa(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        texto_extraido = "política privacidad datos " * 30

        with patch(
            "app.api.v1.ingesta.extraer_texto_url",
            return_value=texto_extraido,
        ):
            response = await client.post(
                "/api/ingesta/url",
                json={"url": "https://ejemplo.com/privacidad"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["fuente"] == "https://ejemplo.com/privacidad"
        assert data["palabras"] == 90

    async def test_ingesta_url_error_extraccion_retorna_422(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")

        with patch(
            "app.api.v1.ingesta.extraer_texto_url",
            side_effect=ExtraccionURLError("No se pudo conectar."),
        ):
            response = await client.post(
                "/api/ingesta/url",
                json={"url": "https://ejemplo.com/privacidad"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 422
