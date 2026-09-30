"""Tests del Motor de Análisis.

- TestSegmentacion: pruebas unitarias de segmentar_politica (función pura)
- TestPrompts: pruebas de construcción de prompts (funciones puras)
- TestParseoJSON: pruebas de parseo y validación de respuesta del LLM
- TestResumen: pruebas de cálculo del resumen general
- TestEndpointsAnalisis: integración con los endpoints /api/analisis/*
"""

import asyncio
import json
from datetime import datetime, timezone
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
                "tipo_tratamiento": "Uso y finalidad de los datos",
                "fragmentos": [1]
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

    def test_analiza_todas_las_secciones_sin_tope(self):
        from app.services.analisis_service import segmentar_politica

        # 15 secciones numeradas: antes solo se conservaban las 8 primeras.
        bloques = []
        for i in range(1, 16):
            bloques.append(f"{i}. Sección {i}\n" + "palabra " * 50)
        texto = "\n\n".join(bloques)
        secciones = segmentar_politica(texto)
        assert len(secciones) == 15
        assert secciones[-1].startswith("15. Sección 15")

    def test_texto_sin_encabezados_se_cubre_completo(self):
        from app.services.analisis_service import _TAM_BLOQUE, segmentar_politica

        # ~30,000 palabras corridas (una política de unos 200,000 caracteres).
        palabras = [f"p{i}" for i in range(30_000)]
        secciones = segmentar_politica(" ".join(palabras))

        assert len(secciones) == 30_000 // _TAM_BLOQUE
        assert " ".join(secciones).split() == palabras

    def test_las_secciones_largas_se_dividen_sin_perder_texto(self):
        from app.services.analisis_service import _MAX_PALABRAS_SECCION, segmentar_politica

        larga = "1. Datos que recopilamos\n" + " ".join(f"d{i}" for i in range(1_600))
        corta = "2. Contacto\n" + "escríbenos a privacidad@ejemplo.com para cualquier duda. " * 6
        secciones = segmentar_politica(larga + "\n\n" + corta)

        assert all(len(s.split()) <= _MAX_PALABRAS_SECCION for s in secciones)
        assert len(secciones) == 5  # 1,604 palabras en bloques de 500 (con el resto unido) + la corta
        assert secciones[-1].startswith("2. Contacto")
        texto_largo = " ".join(secciones[:-1]).split()
        assert texto_largo == larga.split()

    def test_un_resto_muy_corto_se_une_al_bloque_anterior(self):
        from app.services.analisis_service import _TAM_BLOQUE, segmentar_politica

        secciones = segmentar_politica(" ".join(f"p{i}" for i in range(_TAM_BLOQUE * 2 + 5)))

        assert len(secciones) == 2
        assert len(secciones[-1].split()) == _TAM_BLOQUE + 5

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
                    "tipo_tratamiento": "Transferencia de datos a terceros",
                    "fragmentos": [1]
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
                    "tipo_tratamiento": "Tiempo de conservación de los datos",
                    "fragmentos": []
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

async def _esperar_estado_final(client, headers, analisis_id, intentos=200, espera=0.05) -> dict:
    """Sondea GET /estado hasta que el análisis deje de estar 'procesando'
    (o se agoten los intentos: hasta 10 s, margen para máquinas lentas; en
    una máquina normal termina en pocas décimas de segundo). Usado por los tests de integración de HU-13,
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
            privacy_accepted_at=datetime.now(timezone.utc),
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


# ---------------------------------------------------------------------------
# Tipo de tratamiento de datos por hallazgo (lista cerrada)
# ---------------------------------------------------------------------------

def _respuesta_con_tipo(tipo_tratamiento) -> str:
    datos = json.loads(_respuesta_llm_valida())
    if tipo_tratamiento is None:
        datos["hallazgos"][0].pop("tipo_tratamiento")
    else:
        datos["hallazgos"][0]["tipo_tratamiento"] = tipo_tratamiento
    return json.dumps(datos)


class TestTipoTratamiento:
    def test_la_lista_cerrada_tiene_los_textos_exactos(self):
        from app.schemas.analysis import TIPOS_TRATAMIENTO

        assert TIPOS_TRATAMIENTO == (
            "Recopilación de datos personales",
            "Uso y finalidad de los datos",
            "Transferencia de datos a terceros",
            "Tiempo de conservación de los datos",
            "Seguridad de los datos",
            "Derechos del usuario sobre sus datos",
            "Cambios en la política",
            "Otro",
        )

    def test_la_instruccion_al_modelo_incluye_toda_la_lista(self):
        from app.schemas.analysis import TIPOS_TRATAMIENTO
        from app.services.analisis_service import SYSTEM_PROMPT, _construir_prompt_seccion

        for tipo in TIPOS_TRATAMIENTO:
            assert f"   - {tipo}\n" in SYSTEM_PROMPT
        assert '"tipo_tratamiento"' in _construir_prompt_seccion("sección", "contexto")

    def test_categoria_valida_aceptada(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_respuesta_con_tipo("Seguridad de los datos"))
        assert seccion.hallazgos[0].tipo_tratamiento == "Seguridad de los datos"

    def test_tolera_mayusculas_y_espacios_y_guarda_el_texto_exacto(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_respuesta_con_tipo("  transferencia de datos   a TERCEROS "))
        assert seccion.hallazgos[0].tipo_tratamiento == "Transferencia de datos a terceros"

    @pytest.mark.parametrize("invalido", ["Publicidad", "", 3, None])
    def test_categoria_invalida_o_ausente_se_rechaza(self, invalido):
        from app.services.analisis_service import _parsear_seccion

        with pytest.raises(ValueError, match="tipo_tratamiento"):
            _parsear_seccion(_respuesta_con_tipo(invalido))

    def test_la_seccion_de_respaldo_usa_otro(self):
        from app.services.analisis_service import _seccion_fallback

        assert _seccion_fallback("texto", 1).hallazgos[0].tipo_tratamiento == "Otro"

    async def _analizar(self, db_session, seed_user, respuestas):
        from app.services.analisis_service import crear_analisis, ejecutar_analisis_background

        texto = "1. Recopilación\n" + "Recopilamos su nombre y correo para operar el servicio. " * 10
        registro = await crear_analisis(db_session, texto, seed_user.id)
        with patch("app.services.analisis_service.segmentar_politica", return_value=[texto]), \
             patch("app.services.analisis_service.recuperar_contexto", return_value=[]), \
             patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
            llm = MockLLM.return_value
            llm.generar_analisis = AsyncMock(side_effect=respuestas)
            await ejecutar_analisis_background(registro.id, texto)
        await db_session.refresh(registro)
        return registro, llm.generar_analisis

    async def test_categoria_invalida_activa_el_reintento(self, db_session, seed_user):
        registro, llamadas = await self._analizar(db_session, seed_user, [
            _respuesta_con_tipo("Publicidad"),
            _respuesta_con_tipo("Recopilación de datos personales"),
        ])

        assert llamadas.await_count == 2
        # El reintento repite la instrucción completa (con la sección) y el motivo.
        segundo_prompt = llamadas.await_args_list[1].args[1]
        assert "Recopilamos su nombre y correo" in segundo_prompt
        assert "tipo_tratamiento fuera de la lista cerrada" in segundo_prompt
        hallazgo = registro.resultado["secciones_analizadas"][0]["hallazgos"][0]
        assert hallazgo["tipo_tratamiento"] == "Recopilación de datos personales"

    async def test_si_el_reintento_tambien_falla_se_usa_el_respaldo(self, db_session, seed_user):
        registro, llamadas = await self._analizar(db_session, seed_user, [
            _respuesta_con_tipo(None),
            _respuesta_con_tipo("Publicidad"),
        ])

        assert llamadas.await_count == 2
        hallazgo = registro.resultado["secciones_analizadas"][0]["hallazgos"][0]
        assert hallazgo["tipo"] == "neutral"
        assert hallazgo["tipo_tratamiento"] == "Otro"

    async def test_los_analisis_antiguos_sin_el_campo_siguen_mostrandose(
        self, client, db_session, seed_user
    ):
        from app.core.security import create_access_token
        from app.models.analysis import AnalysisTemp

        resultado_antiguo = {
            "id_analisis": "1",
            "fecha": "2026-06-01T12:00:00Z",
            "resumen_general": {"nivel_riesgo_global": "medio", "puntaje": 50, "comentario_breve": "c"},
            "secciones_analizadas": [{
                **{k: v for k, v in json.loads(_respuesta_llm_valida()).items() if k != "hallazgos"},
                "hallazgos": [{
                    "tipo": "riesgo",
                    "descripcion": "Hallazgo previo a la clasificación.",
                    "nivel": "medio",
                    "fuentes_normativas": [],
                }],
            }],
            "recomendaciones": [],
        }
        registro = AnalysisTemp(
            user_id=seed_user.id, texto_original="t", estado="completado", resultado=resultado_antiguo,
        )
        db_session.add(registro)
        await db_session.flush()
        headers = {"Authorization": f"Bearer {create_access_token(str(seed_user.id))}"}

        r = await client.get(f"/api/analisis/{registro.id}", headers=headers)
        pdf = await client.get(f"/api/analisis/{registro.id}/pdf", headers=headers)

        assert r.status_code == 200
        assert r.json()["secciones_analizadas"][0]["hallazgos"][0]["tipo_tratamiento"] is None
        assert pdf.status_code == 200


# ---------------------------------------------------------------------------
# Cobertura completa y análisis en paralelo
# ---------------------------------------------------------------------------

class TestAnalisisEnParalelo:
    async def _analizar(self, db_session, seed_user, secciones, generar):
        from app.services.analisis_service import crear_analisis, ejecutar_analisis_background

        texto = "\n\n".join(secciones)
        registro = await crear_analisis(db_session, texto, seed_user.id)
        with patch("app.services.analisis_service.segmentar_politica", return_value=secciones), \
             patch("app.services.analisis_service.recuperar_contexto", return_value=[]), \
             patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
            MockLLM.return_value.generar_analisis = generar
            await ejecutar_analisis_background(registro.id, texto)
        await db_session.refresh(registro)
        return registro

    @staticmethod
    def _respuesta_para(user_msg: str) -> str:
        datos = json.loads(_respuesta_llm_valida())
        # El título identifica a qué sección corresponde la respuesta.
        datos["titulo"] = user_msg.split('"""')[1].strip().split()[0]
        return json.dumps(datos)

    async def test_conserva_el_orden_y_completa_el_progreso(self, db_session, seed_user):
        secciones = [f"S{i} " + "texto de la sección " * 10 for i in range(1, 13)]

        async def generar(_sistema, user_msg, _contexto):
            # Las primeras secciones tardan más: terminan en otro orden.
            numero = int(user_msg.split('"""')[1].strip().split()[0][1:])
            await asyncio.sleep(0.02 * (13 - numero))
            return self._respuesta_para(user_msg)

        registro = await self._analizar(db_session, seed_user, secciones, generar)

        assert registro.estado == "completado"
        assert registro.secciones_total == registro.seccion_actual == 12
        titulos = [s["titulo"] for s in registro.resultado["secciones_analizadas"]]
        assert titulos == [f"S{i}" for i in range(1, 13)]

    async def test_no_supera_el_limite_de_llamadas_simultaneas(self, db_session, seed_user):
        from app.services.analisis_service import _CONCURRENCIA_LLM

        activas = 0
        maximo = 0

        async def generar(_sistema, user_msg, _contexto):
            nonlocal activas, maximo
            activas += 1
            maximo = max(maximo, activas)
            await asyncio.sleep(0.02)
            activas -= 1
            return self._respuesta_para(user_msg)

        secciones = [f"S{i} " + "texto " * 40 for i in range(1, 11)]
        await self._analizar(db_session, seed_user, secciones, generar)

        assert maximo == _CONCURRENCIA_LLM

    async def test_una_seccion_fallida_no_afecta_a_las_demas(self, db_session, seed_user):
        from app.core.exceptions import LLMError

        async def generar(_sistema, user_msg, _contexto):
            if user_msg.split('"""')[1].strip().startswith("S2 "):
                raise LLMError("fallo simulado")
            return self._respuesta_para(user_msg)

        secciones = [f"S{i} " + "texto " * 40 for i in range(1, 4)]
        registro = await self._analizar(db_session, seed_user, secciones, generar)

        analizadas = registro.resultado["secciones_analizadas"]
        assert [s["titulo"] for s in analizadas] == ["S1", "Sección 2", "S3"]
        assert analizadas[1]["hallazgos"][0]["tipo"] == "neutral"
        assert registro.seccion_actual == 3


# ---------------------------------------------------------------------------
# Citas construidas con los fragmentos reales del corpus (RN-06)
# ---------------------------------------------------------------------------

def _fragmento(id_, documento, jurisdiccion, texto):
    from app.models.corpus import CorpusChunk

    return CorpusChunk(
        id=id_, documento_fuente=documento, jurisdiccion=jurisdiccion,
        referencia=documento, categoria_tematica="general", texto_original=texto, metadatos={},
    )


def _respuesta_con_fragmentos(*listas) -> str:
    datos = json.loads(_respuesta_llm_valida())
    base = datos["hallazgos"][0]
    datos["hallazgos"] = [{**base, "tipo": "riesgo", "nivel": "alto", "fragmentos": f} for f in listas]
    return json.dumps(datos)


FRAGMENTOS = [
    _fragmento(10, "RGPD.pdf", "internacional",
               "Artículo 5. Los datos personales serán tratados de manera   lícita, leal y transparente."),
    _fragmento(20, "Decreto 57-2008 (Ley de Acceso a la Información Pública).pdf", "guatemala",
               "Artículo 9. Datos personales: los relativos a cualquier información concerniente "
               "a personas naturales. Artículo 10. Datos sensibles."),
]


class TestCitasDelCorpus:
    def test_la_cita_usa_el_texto_real_del_fragmento_indicado(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_respuesta_con_fragmentos([2]), FRAGMENTOS)

        hallazgo = seccion.hallazgos[0]
        assert hallazgo.sin_respaldo is False
        [fuente] = hallazgo.fuentes_normativas
        assert fuente.documento == "Decreto 57-2008 (Ley de Acceso a la Información Pública)"
        assert fuente.jurisdiccion == "guatemala"
        assert fuente.referencia == "Artículos 9 y 10"
        assert fuente.fragmento_relevante.startswith("Artículo 9. Datos personales")

    def test_varios_fragmentos_sin_repetir_y_espacios_normalizados(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_respuesta_con_fragmentos([1, "2", 1]), FRAGMENTOS)

        fuentes = seccion.hallazgos[0].fuentes_normativas
        assert [f.documento for f in fuentes] == ["RGPD", FRAGMENTOS[1].documento_fuente[:-4]]
        assert fuentes[0].referencia == "Artículo 5"
        assert "lícita, leal y transparente" in fuentes[0].fragmento_relevante

    def test_los_numeros_inexistentes_se_descartan(self):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_respuesta_con_fragmentos([0, 3, 99, "x", 1]), FRAGMENTOS)

        assert [f.documento for f in seccion.hallazgos[0].fuentes_normativas] == ["RGPD"]

    @pytest.mark.parametrize("fragmentos", [[], [7]])
    def test_sin_fragmentos_validos_queda_sin_respaldo(self, fragmentos):
        from app.services.analisis_service import _parsear_seccion

        seccion = _parsear_seccion(_respuesta_con_fragmentos(fragmentos), FRAGMENTOS)

        assert seccion.hallazgos[0].fuentes_normativas == []
        assert seccion.hallazgos[0].sin_respaldo is True

    @pytest.mark.parametrize("valor", [None, "1", {"n": 1}])
    def test_fragmentos_ausentes_o_mal_formados_activan_el_reintento(self, valor):
        from app.services.analisis_service import _parsear_seccion

        datos = json.loads(_respuesta_con_fragmentos([1]))
        if valor is None:
            del datos["hallazgos"][0]["fragmentos"]
        else:
            datos["hallazgos"][0]["fragmentos"] = valor
        with pytest.raises(ValueError, match="fragmentos"):
            _parsear_seccion(json.dumps(datos), FRAGMENTOS)

    def test_el_texto_largo_se_recorta(self):
        from app.services.analisis_service import _LARGO_FRAGMENTO, _parsear_seccion

        largo = [_fragmento(1, "RGPD.pdf", "internacional", "palabra " * 300)]
        fuente = _parsear_seccion(_respuesta_con_fragmentos([1]), largo).hallazgos[0].fuentes_normativas[0]

        assert fuente.fragmento_relevante.endswith("…")
        assert len(fuente.fragmento_relevante) <= _LARGO_FRAGMENTO + 1
        assert fuente.referencia == ""

    def test_los_hallazgos_sin_respaldo_no_suman_al_puntaje(self):
        from app.services.analisis_service import _calcular_resumen, _parsear_seccion

        respaldado = _parsear_seccion(_respuesta_con_fragmentos([1]), FRAGMENTOS)
        respaldado.hallazgos[0].nivel = "bajo"
        sin_respaldo = _parsear_seccion(_respuesta_con_fragmentos([], []), FRAGMENTOS)

        resumen = _calcular_resumen([respaldado, sin_respaldo])

        assert resumen.nivel_riesgo_global == "bajo"
        assert resumen.puntaje == 0

    def test_la_instruccion_pide_numeros_de_fragmento(self):
        from app.services.analisis_service import SYSTEM_PROMPT, _construir_prompt_seccion

        prompt = _construir_prompt_seccion("texto", "[Fragmento 1] ...")
        assert '"fragmentos": [' in prompt
        assert "fragmento_relevante" not in prompt
        assert "Principios generales" not in prompt + SYSTEM_PROMPT

    async def test_el_analisis_completo_guarda_las_citas_reales(self, db_session, seed_user):
        from app.services.analisis_service import _K_GUATEMALA, crear_analisis, ejecutar_analisis_background

        texto = "1. Terceros\n" + "Compartimos sus datos con socios comerciales. " * 10
        registro = await crear_analisis(db_session, texto, seed_user.id)
        recuperar = AsyncMock(return_value=FRAGMENTOS)
        with patch("app.services.analisis_service.segmentar_politica", return_value=[texto]), \
             patch("app.services.analisis_service.recuperar_contexto", recuperar), \
             patch("app.services.analisis_service.OpenAIAdapter") as MockLLM:
            MockLLM.return_value.generar_analisis = AsyncMock(return_value=_respuesta_con_fragmentos([2], []))
            await ejecutar_analisis_background(registro.id, texto)
        await db_session.refresh(registro)

        assert recuperar.await_args.kwargs["k_guatemala"] == _K_GUATEMALA
        respaldado, sin_respaldo = registro.resultado["secciones_analizadas"][0]["hallazgos"]
        assert respaldado["fuentes_normativas"][0]["jurisdiccion"] == "guatemala"
        assert respaldado["sin_respaldo"] is False
        assert sin_respaldo["sin_respaldo"] is True and sin_respaldo["fuentes_normativas"] == []
