"""Tests del Motor de Análisis.

- TestSegmentacion: pruebas unitarias de segmentar_politica (función pura)
- TestPrompts: pruebas de construcción de prompts (funciones puras)
- TestParseoJSON: pruebas de parseo y validación de respuesta del LLM
- TestResumen: pruebas de cálculo del resumen general
- TestEndpointsAnalisis: integración con los endpoints /api/analisis/*
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Segmentación — función pura
# ---------------------------------------------------------------------------

class TestSegmentacion:
    def test_texto_con_encabezados_numerados(self):
        from app.services.analisis_service import segmentar_politica

        texto = (
            "1. Recopilación de datos\n"
            + "Recopilamos tu nombre y correo electrónico cuando te registras. " * 10
            + "\n\n2. Uso de la información\n"
            + "Usamos tus datos para mejorar nuestros servicios y contactarte. " * 10
        )
        secciones = segmentar_politica(texto)
        assert len(secciones) >= 1

    def test_texto_sin_encabezados_produce_bloques(self):
        from app.services.analisis_service import segmentar_politica

        # Texto plano sin encabezados detectables, ~600 palabras
        texto = "Esta es una cláusula de política de privacidad. " * 80
        secciones = segmentar_politica(texto)
        assert len(secciones) >= 1

    def test_texto_muy_corto_puede_producir_una_seccion(self):
        from app.services.analisis_service import segmentar_politica

        texto = "Recopilamos datos básicos para operar el servicio. " * 10
        secciones = segmentar_politica(texto)
        # Puede producir 0 o 1 según el umbral de palabras mínimas
        assert isinstance(secciones, list)

    def test_limita_a_max_secciones(self):
        from app.services.analisis_service import _MAX_SECCIONES, segmentar_politica

        # 15 secciones numeradas
        bloques = []
        for i in range(1, 16):
            bloques.append(f"{i}. Sección {i}\n" + "palabra " * 50)
        texto = "\n\n".join(bloques)
        secciones = segmentar_politica(texto)
        assert len(secciones) <= _MAX_SECCIONES

    def test_texto_vacio_devuelve_lista_vacia(self):
        from app.services.analisis_service import segmentar_politica

        assert segmentar_politica("") == []
        assert segmentar_politica("   ") == []


# ---------------------------------------------------------------------------
# Parseo de JSON del LLM
# ---------------------------------------------------------------------------

class TestParseoJSON:
    def _json_valido(self) -> str:
        return json.dumps({
            "categoria_opp115": "First Party Collection/Use",
            "titulo": "Recopilación de datos",
            "texto_original": "Recopilamos tus datos para operar el servicio.",
            "hallazgos": [
                {
                    "tipo": "riesgo",
                    "descripcion": "Se comparten datos con terceros no identificados.",
                    "nivel": "alto",
                    "fuentes_normativas": [
                        {
                            "documento": "RGPD",
                            "referencia": "Artículo 5",
                            "fragmento_relevante": "Los datos deben ser tratados con transparencia."
                        }
                    ]
                }
            ]
        })

    def test_parsea_json_valido(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(self._json_valido())
        assert seccion.categoria_opp115 == "First Party Collection/Use"
        assert seccion.titulo == "Recopilación de datos"
        assert len(seccion.hallazgos) == 1
        assert seccion.hallazgos[0].nivel == "alto"

    def test_parsea_json_en_bloque_markdown(self):
        from app.services.analisis_service import _parsear_seccion

        json_envuelto = f"```json\n{self._json_valido()}\n```"
        seccion = _parsear_seccion(json_envuelto)
        assert seccion.titulo == "Recopilación de datos"

    def test_parsea_json_con_texto_extra(self):
        from app.services.analisis_service import _parsear_seccion

        texto_con_basura = f"Aquí está el análisis:\n\n{self._json_valido()}\n\nEspero que sea útil."
        seccion = _parsear_seccion(texto_con_basura)
        assert seccion.categoria_opp115 == "First Party Collection/Use"

    def test_json_invalido_lanza_excepcion(self):
        from app.services.analisis_service import _parsear_seccion

        with pytest.raises((json.JSONDecodeError, ValueError, KeyError)):
            _parsear_seccion("esto no es json")

    def test_parsea_hallazgos_sin_fuentes(self):
        from app.services.analisis_service import _parsear_seccion

        datos = {
            "categoria_opp115": "Data Retention",
            "titulo": "Retención de datos",
            "texto_original": "Los datos se guardan indefinidamente.",
            "hallazgos": [
                {
                    "tipo": "riesgo",
                    "descripcion": "No se especifica plazo de retención.",
                    "nivel": "medio",
                    "fuentes_normativas": []
                }
            ]
        }
        seccion = _parsear_seccion(json.dumps(datos))
        assert seccion.hallazgos[0].fuentes_normativas == []


# ---------------------------------------------------------------------------
# Cálculo del resumen general
# ---------------------------------------------------------------------------

class TestResumen:
    def _seccion(self, nivel: str):
        from app.schemas.analysis import FuenteNormativa, Hallazgo, SeccionAnalizada
        return SeccionAnalizada(
            categoria_opp115="General",
            titulo="Sección test",
            texto_original="texto",
            hallazgos=[
                Hallazgo(
                    tipo="riesgo",
                    descripcion="desc",
                    nivel=nivel,
                    fuentes_normativas=[],
                )
            ],
        )

    def test_solo_hallazgos_altos_da_nivel_alto(self):
        from app.services.analisis_service import _calcular_resumen

        secciones = [self._seccion("alto"), self._seccion("alto")]
        resumen = _calcular_resumen(secciones)
        assert resumen.nivel_riesgo_global == "alto"

    def test_solo_hallazgos_bajos_da_nivel_bajo(self):
        from app.services.analisis_service import _calcular_resumen

        secciones = [self._seccion("bajo"), self._seccion("bajo")]
        resumen = _calcular_resumen(secciones)
        assert resumen.nivel_riesgo_global == "bajo"

    def test_puntaje_entre_0_y_100(self):
        from app.services.analisis_service import _calcular_resumen

        secciones = [self._seccion("medio"), self._seccion("alto")]
        resumen = _calcular_resumen(secciones)
        assert 0 <= resumen.puntaje <= 100

    def test_secciones_vacias_devuelve_bajo(self):
        from app.schemas.analysis import SeccionAnalizada
        from app.services.analisis_service import _calcular_resumen

        secciones = [
            SeccionAnalizada(
                categoria_opp115="General",
                titulo="S",
                texto_original="t",
                hallazgos=[],
            )
        ]
        resumen = _calcular_resumen(secciones)
        assert resumen.nivel_riesgo_global == "bajo"


# ---------------------------------------------------------------------------
# Endpoints de análisis — integración
# ---------------------------------------------------------------------------

class TestEndpointsAnalisis:
    def _respuesta_gemini_valida(self) -> str:
        return json.dumps({
            "categoria_opp115": "First Party Collection/Use",
            "titulo": "Recopilación de datos personales",
            "texto_original": "Recopilamos datos para operar el servicio.",
            "hallazgos": [
                {
                    "tipo": "transparencia",
                    "descripcion": "La finalidad está claramente declarada.",
                    "nivel": "bajo",
                    "fuentes_normativas": [
                        {
                            "documento": "Principios OEA 2021",
                            "referencia": "Principio 2",
                            "fragmento_relevante": "Los datos deben tener finalidad declarada."
                        }
                    ]
                }
            ]
        })

    async def test_iniciar_sin_autenticacion_retorna_403(self, client):
        response = await client.post(
            "/api/analisis/iniciar",
            json={"texto": "texto " * 50},
        )
        assert response.status_code == 403

    async def test_iniciar_texto_corto_retorna_422(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        response = await client.post(
            "/api/analisis/iniciar",
            json={"texto": "Muy corto."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_iniciar_analisis_exitoso(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        texto_largo = (
            "Esta política de privacidad describe cómo nuestra empresa recopila, "
            "usa y protege tus datos personales cuando utilizas nuestros servicios. "
            "Al registrarte, aceptas los términos aquí establecidos. "
            "Recopilamos nombre, correo y datos de uso para mejorar la plataforma. "
            "No compartimos tus datos con terceros sin tu consentimiento explícito. "
        ) * 6

        chunks_mock = []  # RAG vacío en tests
        respuesta_mock = self._respuesta_gemini_valida()

        with patch("app.services.analisis_service.recuperar_contexto", return_value=chunks_mock), \
             patch("app.services.analisis_service.GeminiAdapter") as MockGemini:
            instancia = MockGemini.return_value
            instancia.generar_analisis = AsyncMock(return_value=respuesta_mock)

            response = await client.post(
                "/api/analisis/iniciar",
                json={"texto": texto_largo},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 201
        datos = response.json()
        assert "id_analisis" in datos
        assert "resumen_general" in datos
        assert "secciones_analizadas" in datos
        assert "recomendaciones" in datos
        assert datos["resumen_general"]["nivel_riesgo_global"] in ("bajo", "medio", "alto")

    async def test_iniciar_con_gemini_fallido_usa_fallback(self, client):
        from app.core.security import create_access_token
        from app.core.exceptions import LLMError

        token = create_access_token("1")
        texto_largo = (
            "Política de privacidad. Recopilamos datos para operar el servicio. "
            "Los datos son tratados conforme a la normativa aplicable. "
        ) * 10

        with patch("app.services.analisis_service.recuperar_contexto", return_value=[]), \
             patch("app.services.analisis_service.GeminiAdapter") as MockGemini:
            instancia = MockGemini.return_value
            instancia.generar_analisis = AsyncMock(
                side_effect=LLMError("Error de red simulado")
            )

            response = await client.post(
                "/api/analisis/iniciar",
                json={"texto": texto_largo},
                headers={"Authorization": f"Bearer {token}"},
            )

        # El análisis debe completarse con secciones de fallback
        assert response.status_code == 201
        datos = response.json()
        assert "secciones_analizadas" in datos

    async def test_obtener_analisis_no_existente_retorna_404(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        response = await client.get(
            "/api/analisis/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_obtener_sin_autenticacion_retorna_403(self, client):
        response = await client.get("/api/analisis/1")
        assert response.status_code == 403
