"""Detección de si un texto es una política de privacidad (RN-18).

- TestSenales: vocabulario por temas y voz del responsable
- TestCobertura: semejanza con cláusulas típicas (embeddings simulados)
- TestDecision: umbrales de "politica", "dudosa" y "no_politica"
- TestIngesta / TestInicioAnalisis: la regla en la API
- TestRedDeSeguridad: un análisis sin cláusulas sobre datos no recibe puntuación
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services import deteccion_politica as dp
from app.services.deteccion_politica import Deteccion

POLITICA = (
    "Política de privacidad. Recopilamos tus datos personales cuando creas una cuenta. "
    "Utilizamos tu información para prestar el servicio y compartimos datos con terceros proveedores. "
    "Conservamos los datos durante el plazo necesario. Puedes ejercer tus derechos de acceso y rectificación. "
    "Usamos cookies y aplicamos medidas de seguridad. Si tienes dudas, contáctanos."
)
IMPERSONAL = (
    "Aviso de privacidad. LA EMPRESA recopila los datos personales del usuario, LA EMPRESA utilizará la información "
    "para prestar el servicio y LA EMPRESA podrá compartir los datos con terceros."
)
RECETA = "Pepián de pollo. Tuesta los tomates y los chiles, licúa todo con el caldo y cocina a fuego lento con el pollo."


def _deteccion(resultado: str) -> Deteccion:
    return Deteccion(resultado=resultado, temas_encontrados=[], temas_total=10, cobertura=0.0, voz_responsable=0)


@pytest.fixture(autouse=True)
def limpiar_cache():
    dp.detectar_politica.cache_clear()
    yield
    dp.detectar_politica.cache_clear()


class TestSenales:
    def test_normaliza_mayusculas_tildes_y_espacios(self):
        assert dp.normalizar("Política  de\nPRIVACIDAD") == "politica de privacidad"

    def test_encuentra_los_temas_de_una_politica(self):
        temas = dp.temas_presentes(POLITICA)
        assert {"datos personales", "privacidad", "terceros", "conservacion", "derechos", "cookies"} <= set(temas)

    def test_un_texto_ajeno_no_tiene_temas(self):
        assert dp.temas_presentes(RECETA) == []

    def test_cuenta_la_voz_del_responsable_en_primera_persona(self):
        assert dp.expresiones_responsable(POLITICA) >= 4

    def test_cuenta_la_voz_del_responsable_en_tercera_persona(self):
        assert dp.expresiones_responsable(IMPERSONAL) == 3

    def test_no_confunde_palabras_que_solo_contienen_la_expresion(self):
        assert dp.expresiones_responsable("Los usamosos y recopilamosla no son palabras.") == 0


class TestCobertura:
    def test_mide_la_fraccion_de_fragmentos_parecidos(self, monkeypatch):
        # Prototipos en el eje x; fragmentos alternan cerca y lejos del eje x.
        monkeypatch.setattr(dp, "_vectores_prototipos", None)
        llamadas = []

        def encode_batch(textos):
            llamadas.append(len(textos))
            if len(llamadas) == 1:
                return [[1.0, 0.0] for _ in textos]
            return [[1.0, 0.0] if i % 2 == 0 else [0.0, 1.0] for i in range(len(textos))]

        monkeypatch.setattr(dp.embeddings, "encode_batch", encode_batch)
        texto = " ".join(["palabra"] * (dp._PALABRAS_POR_FRAGMENTO * 4))

        assert dp.cobertura_semantica(texto) == 0.5
        assert llamadas == [len(dp.PROTOTIPOS), 4]

    def test_limita_los_fragmentos_que_compara(self):
        texto = " ".join(["palabra"] * (dp._PALABRAS_POR_FRAGMENTO * (dp._MAX_FRAGMENTOS + 25)))
        assert len(dp._fragmentos(texto)) == dp._MAX_FRAGMENTOS


class TestDecision:
    @pytest.mark.parametrize("temas, cobertura, voz, esperado", [
        (8, 0.9, 40, "politica"),
        (5, 0.30, 3, "politica"),
        (8, 0.9, 0, "dudosa"),      # habla de privacidad, pero no describe prácticas propias
        (4, 0.9, 40, "dudosa"),
        (6, 0.2, 10, "dudosa"),
        (3, 0.1, 0, "dudosa"),
        (2, 0.24, 0, "no_politica"),
        (0, 0.0, 0, "no_politica"),
        (2, 0.25, 0, "dudosa"),
    ])
    def test_umbrales(self, temas, cobertura, voz, esperado):
        assert dp.decidir(temas, cobertura, voz) == esperado

    def test_detecta_y_recuerda_el_resultado(self, monkeypatch):
        cobertura = []
        monkeypatch.setattr(dp, "cobertura_semantica", lambda texto: cobertura.append(texto) or 0.9)

        primera = dp.detectar_politica(POLITICA)
        segunda = dp.detectar_politica(POLITICA)

        assert primera.resultado == "politica"
        assert primera is segunda
        assert len(cobertura) == 1

    def test_una_receta_no_es_una_politica(self, monkeypatch):
        monkeypatch.setattr(dp, "cobertura_semantica", lambda texto: 0.0)
        deteccion = dp.detectar_politica(RECETA)
        assert deteccion.resultado == "no_politica"
        assert deteccion.como_dict()["temas_total"] == len(dp.TEMAS)


class TestIngesta:
    async def test_rechaza_un_texto_que_no_es_una_politica(self, client, monkeypatch):
        from app.core.security import create_access_token

        monkeypatch.setattr("app.api.v1.ingesta.detectar_politica", lambda texto: _deteccion("no_politica"))
        r = await client.post(
            "/api/ingesta/texto", json={"texto": RECETA * 5},
            headers={"Authorization": f"Bearer {create_access_token('1')}"},
        )

        assert r.status_code == 422
        assert "no parece una política de privacidad" in r.json()["detail"]

    async def test_un_texto_dudoso_pasa_con_la_deteccion_para_avisar(self, client, monkeypatch):
        from app.core.security import create_access_token

        monkeypatch.setattr("app.api.v1.ingesta.detectar_politica", lambda texto: _deteccion("dudosa"))
        r = await client.post(
            "/api/ingesta/texto", json={"texto": POLITICA * 3},
            headers={"Authorization": f"Bearer {create_access_token('1')}"},
        )

        assert r.status_code == 200
        assert r.json()["deteccion"]["resultado"] == "dudosa"


class TestInicioAnalisis:
    async def _iniciar(self, client, monkeypatch, resultado, confirma=None):
        from app.core.security import create_access_token

        monkeypatch.setattr("app.api.v1.analisis.detectar_politica", lambda texto: _deteccion(resultado))
        cuerpo = {"texto": POLITICA * 3}
        if confirma is not None:
            cuerpo["confirma_politica"] = confirma
        with patch("app.api.v1.analisis.lanzar_analisis_en_fondo"):
            return await client.post(
                "/api/analisis/iniciar", json=cuerpo,
                headers={"Authorization": f"Bearer {create_access_token('1')}"},
            )

    async def test_un_texto_dudoso_exige_confirmacion(self, client, monkeypatch):
        r = await self._iniciar(client, monkeypatch, "dudosa")
        assert r.status_code == 422
        assert "Confirma que lo es" in r.json()["detail"]

    async def test_un_texto_dudoso_confirmado_se_analiza(self, client, monkeypatch):
        r = await self._iniciar(client, monkeypatch, "dudosa", confirma=True)
        assert r.status_code == 202

    async def test_la_confirmacion_no_salva_un_texto_que_no_es_politica(self, client, monkeypatch):
        r = await self._iniciar(client, monkeypatch, "no_politica", confirma=True)
        assert r.status_code == 422
        assert "no parece una política de privacidad" in r.json()["detail"]


def _seccion(*criterios) -> str:
    return json.dumps({
        "categoria_opp115": "Other", "titulo": "Sección",
        "hallazgos": [
            {"criterio": c, "descripcion": "d", "tipo_tratamiento": "Otro", "fragmentos": []} for c in criterios
        ],
    })


async def _analizar(db_session, user_id, secciones, respuestas):
    from app.services.analisis_service import crear_analisis, ejecutar_analisis_background

    texto = "\n\n".join(secciones)
    registro = await crear_analisis(db_session, texto, user_id)
    with patch("app.services.analisis_service.segmentar_politica", return_value=secciones), \
         patch("app.services.analisis_service.recuperar_contexto", AsyncMock(return_value=[])), \
         patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
        MockLLM.return_value.huellas_sistema = set()
        MockLLM.return_value.generar_analisis = AsyncMock(side_effect=respuestas)
        await ejecutar_analisis_background(registro.id, texto)
    await db_session.refresh(registro)
    return registro


class TestRedDeSeguridad:
    async def test_un_texto_sin_clausulas_sobre_datos_no_recibe_puntuacion(self, client, db_session, seed_user):
        from app.core.security import create_access_token

        secciones = [f"S{i} " + "texto sin datos " * 10 for i in range(5)]
        registro = await _analizar(db_session, seed_user.id, secciones, [_seccion()] * 5)

        assert registro.estado == "error"
        assert registro.resultado == {"motivo_error": "no_es_politica"}
        r = await client.get(
            f"/api/analisis/{registro.id}/estado", headers={"Authorization": f"Bearer {create_access_token('1')}"},
        )
        assert r.json()["motivo"] == "no_es_politica"

    async def test_una_politica_con_hallazgos_se_completa(self, db_session, seed_user):
        secciones = [f"S{i} " + "texto " * 10 for i in range(3)]
        respuestas = [_seccion("A4", "M1"), _seccion(), _seccion("M2")]
        respuestas.append(json.dumps({"recomendaciones": ["Revisa la configuración."]}))

        registro = await _analizar(db_session, seed_user.id, secciones, respuestas)

        assert registro.estado == "completado"

    @pytest.mark.parametrize("hallazgos_por_seccion, esperado", [
        ([0, 0, 0, 0, 0], True),
        ([1, 0, 0, 0, 0, 0], True),     # 1 de 6 secciones y menos de 3 hallazgos
        ([2, 0, 0], False),             # 1 de 3 secciones: proporción suficiente
        ([3, 0, 0, 0, 0, 0], False),    # suficientes hallazgos
        ([], False),                    # nada analizado: no se juzga
    ])
    def test_criterio(self, hallazgos_por_seccion, esperado):
        from app.schemas.analysis import Hallazgo, SeccionAnalizada
        from app.services.analisis_service import _no_parece_politica

        secciones = [
            SeccionAnalizada(
                categoria_opp115="G", titulo="S", texto_original="t",
                hallazgos=[Hallazgo(tipo="riesgo", descripcion="d", nivel="medio", fuentes_normativas=[])] * n,
            )
            for n in hallazgos_por_seccion
        ]
        assert _no_parece_politica(secciones) is esperado

    def test_las_secciones_fallidas_no_cuentan(self):
        from app.schemas.analysis import SeccionAnalizada
        from app.services.analisis_service import _no_parece_politica

        fallida = SeccionAnalizada(categoria_opp115="G", titulo="S", texto_original="t", hallazgos=[], analizada=False)
        assert _no_parece_politica([fallida, fallida]) is False
