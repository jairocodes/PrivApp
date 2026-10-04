"""Tests de la regla única de longitud (RN-01) en las vías de ingesta.

Tras la limpieza: mínimo 200 caracteres y 40 palabras, máximo 300,000.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import TextoDemasiadoCortoError, TextoDemasiadoLargoError
from app.core.security import create_access_token
from app.services.ingesta_service import extraer_texto_url, procesar_texto_directo


def _texto(palabras: int, largo_palabra: int, extra: int = 0) -> str:
    """Texto de `palabras` palabras de `largo_palabra` letras; `extra` alarga la última."""
    lista = ["a" * largo_palabra] * palabras
    lista[-1] += "b" * extra
    return " ".join(lista)


def _por_url(texto: str) -> str:
    respuesta = MagicMock()
    respuesta.text = f"<html><body><main><p>{texto}</p></main></body></html>"
    respuesta.headers = {"content-type": "text/html; charset=utf-8"}
    respuesta.raise_for_status = MagicMock()
    with patch("app.services.ingesta_service.requests.get", return_value=respuesta):
        return extraer_texto_url("https://ejemplo.com/privacidad")


VIAS = [pytest.param(procesar_texto_directo, id="texto_directo"), pytest.param(_por_url, id="url")]

# 40 palabras de 4 letras con 39 espacios = 199 caracteres.
CARACTERES_199 = _texto(40, 4)
CARACTERES_200 = _texto(40, 4, extra=1)
# 39 y 40 palabras de 5 letras (233 y 239 caracteres).
PALABRAS_39 = _texto(39, 5)
PALABRAS_40 = _texto(40, 5)
# 60,000 palabras de 4 letras con 59,999 espacios = 299,999 caracteres.
CARACTERES_300000 = _texto(60_000, 4, extra=1)
CARACTERES_300001 = _texto(60_000, 4, extra=2)


def test_los_textos_de_prueba_tienen_la_longitud_esperada():
    assert len(CARACTERES_199) == 199 and len(CARACTERES_200) == 200
    assert len(PALABRAS_39.split()) == 39 and len(PALABRAS_40.split()) == 40
    assert len(CARACTERES_300000) == 300_000 and len(CARACTERES_300001) == 300_001


@pytest.mark.parametrize("via", VIAS)
class TestLimitesDeLongitud:
    def test_199_caracteres_se_rechaza(self, via):
        with pytest.raises(TextoDemasiadoCortoError):
            via(CARACTERES_199)

    def test_200_caracteres_se_acepta(self, via):
        assert via(CARACTERES_200) == CARACTERES_200

    def test_39_palabras_se_rechaza(self, via):
        with pytest.raises(TextoDemasiadoCortoError):
            via(PALABRAS_39)

    def test_40_palabras_se_acepta(self, via):
        assert via(PALABRAS_40) == PALABRAS_40

    def test_300000_caracteres_se_acepta(self, via):
        assert len(via(CARACTERES_300000)) == 300_000

    def test_mas_de_300000_caracteres_se_rechaza(self, via):
        with pytest.raises(TextoDemasiadoLargoError):
            via(CARACTERES_300001)

    def test_la_regla_se_aplica_despues_de_la_limpieza(self, via):
        # 30 palabras separadas por muchos espacios: más de 200 caracteres
        # en crudo, pero la limpieza los colapsa y queda por debajo del mínimo.
        crudo = "          ".join(["palabra"] * 30)
        assert len(crudo) > 200
        with pytest.raises(TextoDemasiadoCortoError):
            via(crudo)


class TestLongitudEnLosEndpoints:
    async def test_texto_directo_por_debajo_del_minimo_devuelve_422_con_la_regla(self, client):
        token = create_access_token("1")
        r = await client.post(
            "/api/ingesta/texto",
            json={"texto": PALABRAS_39},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422
        assert r.json()["detail"] == "El texto debe tener al menos 200 caracteres y 40 palabras."

    async def test_texto_crudo_largo_que_cumple_tras_limpiar_se_acepta(self, client):
        # 300,500 caracteres en crudo (por espacios repetidos) que quedan en
        # rango tras la limpieza: antes se rechazaba sin limpiar.
        crudo = CARACTERES_200 + " " * 300_300
        assert len(crudo) > 300_000
        token = create_access_token("1")
        r = await client.post(
            "/api/ingesta/texto",
            json={"texto": crudo},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["texto_procesado"] == CARACTERES_200


class TestConteoEnLaRespuesta:
    async def test_texto_directo_informa_caracteres_y_palabras(self, client):
        token = create_access_token("1")
        r = await client.post(
            "/api/ingesta/texto",
            json={"texto": f"  {PALABRAS_40}  "},
            headers={"Authorization": f"Bearer {token}"},
        )
        datos = r.json()
        assert datos["caracteres"] == len(PALABRAS_40) == 239
        assert datos["palabras"] == 40

    async def test_url_informa_caracteres_y_palabras(self, client):
        token = create_access_token("1")
        with patch("app.api.v1.ingesta.extraer_texto_url", return_value=PALABRAS_40):
            r = await client.post(
                "/api/ingesta/url",
                json={"url": "https://ejemplo.com/privacidad"},
                headers={"Authorization": f"Bearer {token}"},
            )
        datos = r.json()
        assert datos["caracteres"] == 239
        assert datos["palabras"] == 40


class TestLongitudAlIniciarAnalisis:
    async def test_iniciar_aplica_la_misma_regla_que_la_ingesta(self, client):
        token = create_access_token("1")
        r = await client.post(
            "/api/analisis/iniciar",
            json={"texto": PALABRAS_39},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422
        assert r.json()["detail"] == "El texto debe tener al menos 200 caracteres y 40 palabras."

    async def test_iniciar_rechaza_mas_de_300000_caracteres(self, client):
        token = create_access_token("1")
        r = await client.post(
            "/api/analisis/iniciar",
            json={"texto": CARACTERES_300001},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422

    async def test_el_mensaje_dice_cuanto_mide_el_texto_y_que_hacer(self, client):
        token = create_access_token("1")
        r = await client.post(
            "/api/ingesta/texto",
            json={"texto": CARACTERES_300001},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422
        detalle = r.json()["detail"]
        assert detalle.startswith("Esta política tiene 300,001 caracteres y el máximo es 300,000.")
        assert "copia solo la parte general" in detalle
