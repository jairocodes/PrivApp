"""Tests del Motor de Análisis.

- TestSegmentacion: pruebas unitarias de segmentar_politica (función pura)
- TestPrompts: pruebas de construcción de prompts (funciones puras)
- TestParseoJSON: pruebas de parseo y validación de respuesta del LLM
- TestResumen: pruebas de cálculo del resumen general
- TestEndpointsAnalisis: integración con los endpoints /api/analisis/*
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _respuesta_llm_valida() -> str:
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

async def _esperar_estado_final(client, headers, analisis_id, intentos=40, espera=0.05) -> dict:
    """Sondea GET /estado hasta que el análisis deje de estar 'procesando'
    (o se agoten los intentos). Usado por los tests de integración de HU-13,
    donde el análisis corre en una tarea de fondo real (asyncio.create_task)
    y no de forma inline como bajo ASGITransport con BackgroundTasks."""
    for _ in range(intentos):
        response = await client.get(f"/api/analisis/{analisis_id}/estado", headers=headers)
        datos = response.json()
        if datos["estado"] != "procesando":
            return datos
        await asyncio.sleep(espera)
    raise AssertionError(f"El análisis {analisis_id} no terminó tras {intentos} intentos.")


class TestEndpointsAnalisis:
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
        headers = {"Authorization": f"Bearer {token}"}
        texto_largo = (
            "Esta política de privacidad describe cómo nuestra empresa recopila, "
            "usa y protege tus datos personales cuando utilizas nuestros servicios. "
            "Al registrarte, aceptas los términos aquí establecidos. "
            "Recopilamos nombre, correo y datos de uso para mejorar la plataforma. "
            "No compartimos tus datos con terceros sin tu consentimiento explícito. "
        ) * 6

        with patch("app.services.analisis_service.recuperar_contexto", return_value=[]), \
             patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
            instancia = MockLLM.return_value
            instancia.generar_analisis = AsyncMock(return_value=_respuesta_llm_valida())

            response = await client.post(
                "/api/analisis/iniciar", json={"texto": texto_largo}, headers=headers,
            )
            assert response.status_code == 202
            iniciado = response.json()
            assert iniciado["estado"] == "procesando"
            analisis_id = iniciado["id_analisis"]

            estado_final = await _esperar_estado_final(client, headers, analisis_id)
            assert estado_final["estado"] == "completado"
            assert estado_final["seccion_actual"] == estado_final["secciones_total"]

            respuesta = await client.get(f"/api/analisis/{analisis_id}", headers=headers)

        assert respuesta.status_code == 200
        datos = respuesta.json()
        assert datos["id_analisis"] == analisis_id
        assert "resumen_general" in datos
        assert "secciones_analizadas" in datos
        assert "recomendaciones" in datos
        assert datos["resumen_general"]["nivel_riesgo_global"] in ("bajo", "medio", "alto")

    async def test_iniciar_con_llm_fallido_usa_fallback(self, client):
        from app.core.security import create_access_token
        from app.core.exceptions import LLMError

        token = create_access_token("1")
        headers = {"Authorization": f"Bearer {token}"}
        texto_largo = (
            "Política de privacidad. Recopilamos datos para operar el servicio. "
            "Los datos son tratados conforme a la normativa aplicable. "
        ) * 10

        with patch("app.services.analisis_service.recuperar_contexto", return_value=[]), \
             patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
            instancia = MockLLM.return_value
            instancia.generar_analisis = AsyncMock(
                side_effect=LLMError("Error de red simulado")
            )

            response = await client.post(
                "/api/analisis/iniciar", json={"texto": texto_largo}, headers=headers,
            )
            assert response.status_code == 202
            analisis_id = response.json()["id_analisis"]

            estado_final = await _esperar_estado_final(client, headers, analisis_id)
            # El análisis debe completarse con secciones de fallback, no quedar en error
            assert estado_final["estado"] == "completado"

            respuesta = await client.get(f"/api/analisis/{analisis_id}", headers=headers)

        assert respuesta.status_code == 200
        assert "secciones_analizadas" in respuesta.json()

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

    async def test_obtener_analisis_en_procesamiento_retorna_404(self, client, db_session, seed_user):
        from app.core.security import create_access_token
        from app.models.analysis import AnalysisTemp

        registro = AnalysisTemp(
            user_id=seed_user.id, texto_original="texto", estado="procesando", seccion_actual=0,
        )
        db_session.add(registro)
        await db_session.commit()

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            f"/api/analisis/{registro.id}", headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestEstadoYProgreso:
    async def test_estado_sin_autenticacion_retorna_403(self, client):
        response = await client.get("/api/analisis/1/estado")
        assert response.status_code == 403

    async def test_estado_no_existente_retorna_404(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        response = await client.get(
            "/api/analisis/99999/estado", headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_estado_de_otro_usuario_retorna_404(self, client, db_session, seed_user):
        from app.core.security import create_access_token, hash_password
        from app.models.analysis import AnalysisTemp
        from app.models.user import User

        otro_usuario = User(
            nombre="Otro Usuario", email="otro-estado@privapp.test",
            hashed_password=hash_password("OtraPass123"), is_active=True,
        )
        db_session.add(otro_usuario)
        await db_session.flush()

        registro = AnalysisTemp(
            user_id=otro_usuario.id, texto_original="texto", estado="procesando", seccion_actual=0,
        )
        db_session.add(registro)
        await db_session.commit()

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            f"/api/analisis/{registro.id}/estado", headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_estado_en_procesamiento_refleja_seccion_actual(self, client, db_session, seed_user):
        from app.core.security import create_access_token
        from app.models.analysis import AnalysisTemp

        registro = AnalysisTemp(
            user_id=seed_user.id, texto_original="texto", estado="procesando",
            seccion_actual=1, secciones_total=3,
        )
        db_session.add(registro)
        await db_session.commit()

        token = create_access_token(str(seed_user.id))
        response = await client.get(
            f"/api/analisis/{registro.id}/estado", headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        datos = response.json()
        assert datos == {"estado": "procesando", "seccion_actual": 1, "secciones_total": 3}

    async def test_ejecutar_analisis_background_completa_y_persiste_resultado(
        self, db_session, seed_user
    ):
        from app.services.analisis_service import crear_analisis, ejecutar_analisis_background

        texto_largo = "Política de privacidad de prueba. " * 60
        registro = await crear_analisis(db_session, texto_largo, seed_user.id)

        with patch("app.services.analisis_service.recuperar_contexto", return_value=[]), \
             patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
            instancia = MockLLM.return_value
            instancia.generar_analisis = AsyncMock(return_value=_respuesta_llm_valida())
            await ejecutar_analisis_background(registro.id, texto_largo)

        await db_session.refresh(registro)
        assert registro.estado == "completado"
        assert registro.secciones_total is not None
        assert registro.seccion_actual == registro.secciones_total
        assert registro.resultado is not None

    async def test_ejecutar_analisis_background_fallo_marca_estado_error(
        self, db_session, seed_user
    ):
        from app.services.analisis_service import crear_analisis, ejecutar_analisis_background

        texto_largo = "Política de privacidad de prueba. " * 60
        registro = await crear_analisis(db_session, texto_largo, seed_user.id)

        with patch(
            "app.services.analisis_service.segmentar_politica",
            side_effect=RuntimeError("fallo simulado"),
        ):
            await ejecutar_analisis_background(registro.id, texto_largo)

        await db_session.refresh(registro)
        assert registro.estado == "error"

    async def test_iniciar_dispara_tarea_en_segundo_plano_que_completa(self, client):
        from app.core.security import create_access_token

        token = create_access_token("1")
        headers = {"Authorization": f"Bearer {token}"}
        texto_largo = "Política de privacidad de prueba para integración. " * 20

        with patch("app.services.analisis_service.recuperar_contexto", return_value=[]), \
             patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
            instancia = MockLLM.return_value
            instancia.generar_analisis = AsyncMock(return_value=_respuesta_llm_valida())

            response = await client.post(
                "/api/analisis/iniciar", json={"texto": texto_largo}, headers=headers,
            )
            assert response.status_code == 202
            analisis_id = response.json()["id_analisis"]

            estado_final = await _esperar_estado_final(client, headers, analisis_id)

        assert estado_final["estado"] == "completado"
