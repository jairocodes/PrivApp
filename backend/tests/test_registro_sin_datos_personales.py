"""Los registros del servidor no deben contener datos personales."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from app.core.registro import IP_OMITIDA, OcultarIpLimitador


def _texto(caplog) -> str:
    return "\n".join(r.getMessage() for r in caplog.records)


class TestCorreos:
    async def test_el_registro_no_escribe_el_correo(self, client, caplog):
        caplog.set_level(logging.INFO)
        r = await client.post("/api/auth/register", json={
            "nombre": "Persona Nueva", "email": "persona.nueva@ejemplo.com",
            "password": "ClaveSegura1", "acepta_aviso": True,
        })
        assert r.status_code == 201
        assert "persona.nueva@ejemplo.com" not in _texto(caplog)

    async def test_un_inicio_fallido_no_escribe_el_correo(self, client, caplog):
        caplog.set_level(logging.INFO)
        await client.post("/api/auth/login", json={"email": "alguien@ejemplo.com", "password": "Otra12345"})
        texto = _texto(caplog)
        assert "Intento de inicio de sesión fallido." in texto
        assert "alguien@ejemplo.com" not in texto


class TestDireccionesWeb:
    URL = "https://www.ejemplo.com/privacidad?usuario=ana.lopez&token=abc123"

    def _respuesta(self):
        respuesta = MagicMock(headers={"content-type": "text/html"})
        respuesta.text = "<main>" + "<p>Recopilamos tus datos personales para operar.</p>" * 40 + "</main>"
        return respuesta

    def test_solo_se_registra_el_nombre_del_sitio(self, caplog):
        from app.services.ingesta_service import extraer_texto_url

        caplog.set_level(logging.INFO)
        with patch("app.services.ingesta_service.requests.get", return_value=self._respuesta()):
            extraer_texto_url(self.URL)

        texto = _texto(caplog)
        assert "www.ejemplo.com" in texto
        assert "ana.lopez" not in texto and "/privacidad" not in texto

    def test_los_errores_tampoco_registran_la_direccion(self, caplog):
        import requests

        from app.core.exceptions import ExtraccionURLError
        from app.services.ingesta_service import extraer_texto_url

        caplog.set_level(logging.INFO)
        with patch("app.services.ingesta_service.requests.get", side_effect=requests.exceptions.Timeout()):
            with pytest.raises(ExtraccionURLError):
                extraer_texto_url(self.URL)
        assert "ana.lopez" not in _texto(caplog)


class TestArchivos:
    def test_el_nombre_del_archivo_no_se_registra(self, caplog):
        from app.services.ingesta_service import procesar_archivo
        from tests.pdf_de_prueba import pdf_con_texto

        caplog.set_level(logging.DEBUG)
        procesar_archivo(
            "Política de Ana López.pdf", "application/pdf",
            pdf_con_texto(["Recopilamos tus datos personales para operar el servicio."] * 30),
        )
        assert "Ana López" not in _texto(caplog)


class TestIpDelLimitador:
    def test_el_aviso_de_limite_superado_oculta_la_ip(self):
        registro = logging.LogRecord(
            "slowapi", logging.WARNING, __file__, 1,
            "ratelimit %s (%s) exceeded at endpoint: %s", ("5 per 1 minute", "203.0.113.7", "/api/auth/login"), None,
        )

        assert OcultarIpLimitador().filter(registro) is True
        mensaje = registro.getMessage()
        assert "203.0.113.7" not in mensaje
        assert IP_OMITIDA in mensaje and "/api/auth/login" in mensaje

    def test_los_demas_mensajes_no_cambian(self):
        registro = logging.LogRecord(
            "slowapi", logging.INFO, __file__, 1, "Storage has been reset and all limits cleared", (), None,
        )
        OcultarIpLimitador().filter(registro)
        assert registro.getMessage() == "Storage has been reset and all limits cleared"

    def test_el_filtro_esta_instalado_en_el_registro_de_slowapi(self):
        import app.main  # noqa: F401  (configura el registro al importarse)

        assert any(isinstance(f, OcultarIpLimitador) for f in logging.getLogger("slowapi").filters)
