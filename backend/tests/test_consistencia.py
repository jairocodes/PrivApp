"""Consistencia del análisis: el mismo texto debe dar el mismo resultado.

- TestParametrosDelModelo: temperatura, semilla y salidas estructuradas estrictas
- TestNivelDesdeCriterio: el nivel y el tipo de cada hallazgo los fija el criterio
- TestReintentoTransitorio: una sección no se pierde por un error momentáneo
- TestReutilizacion: un texto idéntico reutiliza el resultado anterior
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from openai import APIConnectionError

from app.services.llm.openai_adapter import OpenAIAdapter


def _respuesta_openai(contenido: str, huella: str | None = "fp_prueba"):
    respuesta = MagicMock()
    respuesta.choices = [MagicMock(message=MagicMock(content=contenido))]
    respuesta.system_fingerprint = huella
    return respuesta


def _seccion_json(*hallazgos) -> str:
    return json.dumps({
        "categoria_opp115": "Third Party Sharing/Collection",
        "titulo": "Compartición",
        "hallazgos": [
            {"criterio": c, "descripcion": f"Hallazgo {c}", "tipo_tratamiento": "Otro", "fragmentos": []}
            for c in hallazgos
        ],
    })


# ---------------------------------------------------------------------------
# Parámetros enviados a OpenAI
# ---------------------------------------------------------------------------

class TestParametrosDelModelo:
    async def test_envia_temperatura_semilla_y_esquema_estricto(self):
        from app.services.analisis_service import ESQUEMA_SECCION

        adapter = OpenAIAdapter(api_key="fake-key", temperature=0.0, seed=123)
        with patch.object(
            adapter._client.chat.completions, "create", AsyncMock(return_value=_respuesta_openai("{}"))
        ) as create:
            await adapter.generar_analisis("sistema", "mensaje", "", esquema=ESQUEMA_SECCION)

        opciones = create.await_args.kwargs
        assert opciones["temperature"] == 0.0
        assert opciones["seed"] == 123
        assert opciones["response_format"] == {
            "type": "json_schema",
            "json_schema": {**ESQUEMA_SECCION, "strict": True},
        }

    async def test_sin_esquema_pide_json_simple(self):
        adapter = OpenAIAdapter(api_key="fake-key")
        with patch.object(
            adapter._client.chat.completions, "create", AsyncMock(return_value=_respuesta_openai("{}"))
        ) as create:
            await adapter.generar_analisis("sistema", "mensaje", "")

        assert create.await_args.kwargs["response_format"] == {"type": "json_object"}

    async def test_registra_las_huellas_del_sistema(self):
        adapter = OpenAIAdapter(api_key="fake-key")
        respuestas = [_respuesta_openai("{}", "fp_a"), _respuesta_openai("{}", "fp_a"), _respuesta_openai("{}", None)]
        with patch.object(adapter._client.chat.completions, "create", AsyncMock(side_effect=respuestas)):
            for _ in respuestas:
                await adapter.generar_analisis("sistema", "mensaje", "")

        assert adapter.huellas_sistema == {"fp_a"}

    def test_la_fabrica_usa_la_configuracion(self, monkeypatch):
        from app.config import settings
        from app.services.analisis_service import _crear_adaptador_llm

        monkeypatch.setattr(settings, "llm_provider", "openai")
        monkeypatch.setattr(settings, "openai_temperature", 0.0)
        monkeypatch.setattr(settings, "openai_seed", 77)

        adaptador = _crear_adaptador_llm()

        assert adaptador.temperatura == 0.0
        assert adaptador.semilla == 77

    def test_los_esquemas_son_estrictos_y_cerrados(self):
        from app.schemas.analysis import TIPOS_TRATAMIENTO
        from app.services.analisis_service import (
            CRITERIOS, ESQUEMA_RECOMENDACIONES, ESQUEMA_RESPALDO, ESQUEMA_SECCION,
        )

        for esquema in (ESQUEMA_SECCION, ESQUEMA_RESPALDO, ESQUEMA_RECOMENDACIONES):
            raiz = esquema["schema"]
            assert raiz["additionalProperties"] is False
            assert set(raiz["required"]) == set(raiz["properties"])
        hallazgo = ESQUEMA_SECCION["schema"]["properties"]["hallazgos"]["items"]
        assert hallazgo["properties"]["criterio"]["enum"] == list(CRITERIOS)
        assert hallazgo["properties"]["tipo_tratamiento"]["enum"] == list(TIPOS_TRATAMIENTO)
        assert set(hallazgo["required"]) == set(hallazgo["properties"])


# ---------------------------------------------------------------------------
# Nivel y tipo derivados del criterio
# ---------------------------------------------------------------------------

class TestNivelDesdeCriterio:
    def test_la_rubrica_tiene_diecinueve_criterios(self):
        from app.services.analisis_service import CRITERIOS, SYSTEM_PROMPT

        assert len(CRITERIOS) == 19
        for codigo in CRITERIOS:
            assert f"- {codigo}: " in SYSTEM_PROMPT

    @pytest.mark.parametrize("criterio, tipo, nivel", [
        ("A1", "riesgo", "alto"),
        ("A10", "riesgo", "alto"),
        ("M3", "riesgo", "medio"),
        ("B2", "transparencia", "bajo"),
    ])
    def test_el_criterio_fija_tipo_y_nivel(self, criterio, tipo, nivel):
        from app.services.analisis_service import _parsear_seccion

        [hallazgo] = _parsear_seccion(_seccion_json(criterio)).hallazgos

        assert (hallazgo.criterio, hallazgo.tipo, hallazgo.nivel) == (criterio, tipo, nivel)

    def test_ignora_tipo_y_nivel_que_envie_el_modelo(self):
        from app.services.analisis_service import _parsear_seccion

        datos = json.loads(_seccion_json("M1"))
        datos["hallazgos"][0].update({"tipo": "neutral", "nivel": "alto"})

        [hallazgo] = _parsear_seccion(json.dumps(datos)).hallazgos

        assert (hallazgo.tipo, hallazgo.nivel) == ("riesgo", "medio")

    @pytest.mark.parametrize("invalido", ["A11", "Z1", "", None, 3])
    def test_criterio_fuera_de_la_lista_activa_el_reintento(self, invalido):
        from app.services.analisis_service import _parsear_seccion

        datos = json.loads(_seccion_json("A1"))
        datos["hallazgos"][0]["criterio"] = invalido

        with pytest.raises(ValueError):
            _parsear_seccion(json.dumps(datos))

    def test_una_seccion_con_riesgos_no_conserva_buenas_practicas(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_seccion_json("B1", "A4", "B3", "M2"))

        assert [h.criterio for h in seccion.hallazgos] == ["A4", "M2"]

    def test_una_seccion_sin_riesgos_conserva_una_sola_buena_practica(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_seccion_json("B2", "B1", "B4"))

        assert [h.criterio for h in seccion.hallazgos] == ["B2"]

    def test_una_buena_practica_descartada_con_criterio_invalido_activa_el_reintento(self):
        from app.services.analisis_service import _parsear_seccion

        datos = json.loads(_seccion_json("A4", "B1"))
        datos["hallazgos"][1]["criterio"] = "B9"

        with pytest.raises(ValueError):
            _parsear_seccion(json.dumps(datos))

    def test_seccion_sin_criterios_queda_sin_hallazgos(self):
        from app.services.analisis_service import _calcular_resumen, _parsear_seccion

        seccion = _parsear_seccion(_seccion_json())

        assert seccion.hallazgos == []
        assert _calcular_resumen([seccion]).puntaje == 0

    def test_el_texto_original_lo_copia_el_sistema(self):
        from app.services.analisis_service import _LARGO_TEXTO_ORIGINAL, _parsear_seccion

        texto = "Compartimos tus datos con socios. " * 30
        datos = json.loads(_seccion_json("A4"))
        datos["texto_original"] = "texto inventado por el modelo"

        seccion = _parsear_seccion(json.dumps(datos), texto_seccion=texto)

        assert seccion.texto_original == texto[:_LARGO_TEXTO_ORIGINAL]


# ---------------------------------------------------------------------------
# Reintento ante errores transitorios
# ---------------------------------------------------------------------------

def _error_de_conexion() -> APIConnectionError:
    return APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"))


class TestReintentoTransitorio:
    async def test_un_error_transitorio_se_reintenta_una_vez(self):
        from app.services.analisis_service import ESQUEMA_SECCION, _llamar_modelo

        llm = MagicMock()
        llm.generar_analisis = AsyncMock(side_effect=[_error_de_conexion(), "respuesta"])
        with patch("app.services.analisis_service.asyncio.sleep", AsyncMock()) as pausa:
            resultado = await _llamar_modelo(llm, "sistema", "mensaje", ESQUEMA_SECCION, 1)

        assert resultado == "respuesta"
        assert llm.generar_analisis.await_count == 2
        pausa.assert_awaited_once()

    async def test_un_segundo_error_transitorio_se_propaga(self):
        from app.services.analisis_service import ESQUEMA_SECCION, _llamar_modelo

        llm = MagicMock()
        llm.generar_analisis = AsyncMock(side_effect=[_error_de_conexion(), _error_de_conexion()])
        with patch("app.services.analisis_service.asyncio.sleep", AsyncMock()), \
             pytest.raises(APIConnectionError):
            await _llamar_modelo(llm, "sistema", "mensaje", ESQUEMA_SECCION, 1)

    async def test_un_error_definitivo_no_se_reintenta(self):
        from app.core.exceptions import LLMError
        from app.services.analisis_service import ESQUEMA_SECCION, _llamar_modelo

        llm = MagicMock()
        llm.generar_analisis = AsyncMock(side_effect=LLMError("clave inválida"))
        with pytest.raises(LLMError):
            await _llamar_modelo(llm, "sistema", "mensaje", ESQUEMA_SECCION, 1)

        assert llm.generar_analisis.await_count == 1


# ---------------------------------------------------------------------------
# Reutilización del resultado de un texto idéntico
# ---------------------------------------------------------------------------

TEXTO = "Compartimos tus datos con socios comerciales para publicidad. " * 12


async def _analizar(db_session, user_id, texto=TEXTO, respuesta=None, error=None):
    """Ejecuta el análisis completo con el modelo simulado; devuelve el registro y el modelo."""
    from app.services.analisis_service import crear_analisis, ejecutar_analisis_background

    registro = await crear_analisis(db_session, texto, user_id)
    with patch("app.services.analisis_service.segmentar_politica", return_value=[texto]), \
         patch("app.services.analisis_service.recuperar_contexto", AsyncMock(return_value=[])), \
         patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
        llm = MockLLM.return_value
        llm.huellas_sistema = {"fp_prueba"}
        if error is not None:
            llm.generar_analisis = AsyncMock(side_effect=error)
        else:
            llm.generar_analisis = AsyncMock(return_value=respuesta or _seccion_json("A4", "M1"))
        await ejecutar_analisis_background(registro.id, texto)
    await db_session.refresh(registro)
    return registro, llm


class TestReutilizacion:
    def test_la_huella_ignora_espacios_y_saltos_de_linea(self):
        from app.services.analisis_service import huella_texto

        assert huella_texto("Hola  mundo\n\ncruel ") == huella_texto("Hola mundo cruel")
        assert huella_texto("Hola mundo") != huella_texto("Hola Mundo")
        assert len(huella_texto("x")) == 64

    async def test_guarda_la_huella_y_los_metadatos(self, db_session, seed_user):
        from app.config import settings
        from app.services.analisis_service import VERSION_PROMPT, huella_texto

        registro, _ = await _analizar(db_session, seed_user.id)

        assert registro.estado == "completado"
        assert registro.text_hash == huella_texto(TEXTO)
        assert registro.resultado["metadatos_analisis"] == {
            "modelo": settings.openai_model,
            "temperatura": settings.openai_temperature,
            "semilla": settings.openai_seed,
            "version_prompt": VERSION_PROMPT,
            "version_corpus": "corpus-de-prueba",
            "huellas_sistema": ["fp_prueba"],
            "reutilizado_de": None,
        }

    async def test_el_mismo_texto_reutiliza_el_resultado_sin_llamar_al_modelo(self, db_session, seed_user):
        primero, _ = await _analizar(db_session, seed_user.id)
        segundo, llm = await _analizar(db_session, seed_user.id, texto=TEXTO.replace(". ", ".\n"))

        assert llm.generar_analisis.await_count == 0
        assert segundo.estado == "completado"
        assert segundo.resultado["id_analisis"] == str(segundo.id)
        assert segundo.resultado["resumen_general"] == primero.resultado["resumen_general"]
        assert segundo.resultado["secciones_analizadas"] == primero.resultado["secciones_analizadas"]
        assert segundo.resultado["recomendaciones"] == primero.resultado["recomendaciones"]
        assert segundo.resultado["metadatos_analisis"]["reutilizado_de"] == primero.id
        assert segundo.secciones_total == segundo.seccion_actual == 1

    async def test_reutiliza_entre_usuarios_sin_copiar_los_metadatos_del_reporte(self, db_session, seed_user):
        from app.models.user import User

        primero, _ = await _analizar(db_session, seed_user.id)
        primero.resultado = {**primero.resultado, "metadatos_reporte": {"generaciones": [1.0]}}
        otro = User(nombre="Otra", email="otra@ejemplo.com", hashed_password="x", is_active=True,
                    privacy_accepted_at=seed_user.privacy_accepted_at)
        db_session.add(otro)
        await db_session.commit()

        segundo, llm = await _analizar(db_session, otro.id)

        assert llm.generar_analisis.await_count == 0
        assert segundo.user_id == otro.id
        assert "metadatos_reporte" not in segundo.resultado

    async def test_otro_corpus_no_reutiliza(self, db_session, seed_user, monkeypatch):
        await _analizar(db_session, seed_user.id)

        async def otro_corpus(db):
            return "corpus-cambiado"

        monkeypatch.setattr("app.services.analisis_service._version_corpus", otro_corpus)
        segundo, llm = await _analizar(db_session, seed_user.id)

        assert llm.generar_analisis.await_count > 0
        assert segundo.resultado["metadatos_analisis"]["reutilizado_de"] is None

    async def test_otra_version_del_prompt_no_reutiliza(self, db_session, seed_user, monkeypatch):
        await _analizar(db_session, seed_user.id)
        monkeypatch.setattr("app.services.analisis_service.VERSION_PROMPT", "999")

        _, llm = await _analizar(db_session, seed_user.id)

        assert llm.generar_analisis.await_count > 0

    async def test_un_resultado_con_secciones_fallidas_no_se_reutiliza(self, db_session, seed_user):
        from app.core.exceptions import LLMError

        fallido, _ = await _analizar(db_session, seed_user.id, error=LLMError("fallo simulado"))
        assert fallido.resultado["secciones_analizadas"][0]["analizada"] is False

        _, llm = await _analizar(db_session, seed_user.id)

        assert llm.generar_analisis.await_count > 0

    async def test_un_texto_distinto_no_reutiliza(self, db_session, seed_user):
        await _analizar(db_session, seed_user.id)

        _, llm = await _analizar(db_session, seed_user.id, texto=TEXTO + " Cambio.")

        assert llm.generar_analisis.await_count > 0
