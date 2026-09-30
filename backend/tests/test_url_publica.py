"""La ingesta por URL solo descarga sitios web públicos (protección contra SSRF)."""

import socket
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ExtraccionURLError
from app.services.ingesta_service import MENSAJE_URL_NO_PUBLICA, extraer_texto_url, validar_url_publica

HTML = "<html><body><main>" + "<p>Recopilamos tus datos personales para operar el servicio.</p>" * 40 + "</main></body></html>"


def _respuesta(status=200, location=None):
    r = MagicMock()
    r.status_code = status
    r.text = HTML
    r.headers = {"content-type": "text/html"}
    if location:
        r.headers["location"] = location
    return r


def _resolver(mapa):
    return lambda host: mapa[host]


class TestValidacion:
    @pytest.mark.parametrize("ip", [
        "127.0.0.1",          # la propia máquina
        "10.0.0.5",           # red privada
        "172.16.3.4",
        "192.168.1.10",
        "169.254.169.254",    # metadatos de la nube
        "100.64.0.1",         # red compartida del proveedor
        "0.0.0.0",
        "::1",
        "fd00::1",            # IPv6 privada
        "fe80::1%eth0",       # IPv6 de enlace local
        "224.0.0.1",          # multidifusión
    ])
    def test_rechaza_direcciones_no_publicas(self, monkeypatch, ip):
        monkeypatch.setattr("app.services.ingesta_service._resolver_ips", lambda host: [ip])
        with pytest.raises(ExtraccionURLError) as exc:
            validar_url_publica("https://interno.ejemplo.com/politica")
        assert exc.value.detail == MENSAJE_URL_NO_PUBLICA

    def test_rechaza_si_alguna_de_las_ip_es_interna(self, monkeypatch):
        monkeypatch.setattr("app.services.ingesta_service._resolver_ips", lambda host: ["93.184.216.34", "10.0.0.1"])
        with pytest.raises(ExtraccionURLError):
            validar_url_publica("https://mixto.ejemplo.com")

    @pytest.mark.parametrize("url", [
        "ftp://ejemplo.com/politica",
        "file:///etc/passwd",
        "gopher://ejemplo.com",
        "ejemplo.com/politica",
        "http://",
    ])
    def test_solo_http_o_https(self, url):
        with pytest.raises(ExtraccionURLError) as exc:
            validar_url_publica(url)
        assert "http://" in exc.value.detail

    @pytest.mark.parametrize("url", [
        "https://ejemplo.com:6379/",
        "http://ejemplo.com:5432/",
        "https://usuario:clave@ejemplo.com/",
        "https://ejemplo.com:99999/",
    ])
    def test_rechaza_puertos_no_estandar_y_credenciales(self, url):
        with pytest.raises(ExtraccionURLError) as exc:
            validar_url_publica(url)
        assert exc.value.detail == MENSAJE_URL_NO_PUBLICA

    def test_un_sitio_que_no_existe_da_error_de_conexion(self, monkeypatch):
        def fallar(host):
            raise socket.gaierror("no existe")
        monkeypatch.setattr("app.services.ingesta_service._resolver_ips", fallar)
        with pytest.raises(ExtraccionURLError) as exc:
            validar_url_publica("https://no-existe.ejemplo.com")
        assert "conectar" in exc.value.detail

    @pytest.mark.parametrize("url", ["https://ejemplo.com/privacidad", "http://ejemplo.com:80/", "HTTPS://Ejemplo.com:443/p"])
    def test_acepta_sitios_publicos(self, url):
        validar_url_publica(url)


class TestRedirecciones:
    def test_valida_cada_destino_de_una_redireccion(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.ingesta_service._resolver_ips",
            _resolver({"publico.ejemplo.com": ["93.184.216.34"], "interno.ejemplo.com": ["10.0.0.7"]}),
        )
        respuestas = [_respuesta(302, "http://interno.ejemplo.com/admin")]
        with patch("app.services.ingesta_service.requests.get", side_effect=respuestas) as get:
            with pytest.raises(ExtraccionURLError) as exc:
                extraer_texto_url("https://publico.ejemplo.com/politica")

        assert exc.value.detail == MENSAJE_URL_NO_PUBLICA
        assert get.call_count == 1  # nunca se pidió la dirección interna
        assert get.call_args.kwargs["allow_redirects"] is False

    def test_sigue_redirecciones_publicas_relativas(self):
        respuestas = [_respuesta(301, "/es/privacidad"), _respuesta(200)]
        with patch("app.services.ingesta_service.requests.get", side_effect=respuestas) as get:
            texto = extraer_texto_url("https://ejemplo.com/privacy")

        assert "Recopilamos tus datos" in texto
        assert get.call_args_list[1].args[0] == "https://ejemplo.com/es/privacidad"

    def test_limita_la_cantidad_de_redirecciones(self):
        with patch("app.services.ingesta_service.requests.get", return_value=_respuesta(302, "/otra")):
            with pytest.raises(ExtraccionURLError) as exc:
                extraer_texto_url("https://ejemplo.com/bucle")
        assert "redirige demasiadas veces" in exc.value.detail


class TestRuta:
    async def test_la_api_responde_422_con_el_motivo(self, client, seed_user, monkeypatch):
        from app.core.security import create_access_token

        monkeypatch.setattr("app.services.ingesta_service._resolver_ips", lambda host: ["169.254.169.254"])
        with patch("app.services.ingesta_service.requests.get") as get:
            r = await client.post(
                "/api/ingesta/url",
                json={"url": "http://metadata.ejemplo.com/latest/"},
                headers={"Authorization": f"Bearer {create_access_token(str(seed_user.id))}"},
            )

        assert r.status_code == 422
        assert r.json()["detail"] == MENSAJE_URL_NO_PUBLICA
        get.assert_not_called()
