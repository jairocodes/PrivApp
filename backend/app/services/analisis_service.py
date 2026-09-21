"""Motor de Análisis: orquesta segmentación, RAG, prompts y llamada a Gemini.

Flujo completo por política:
1. segmentar_politica(texto)        → list[str]  (secciones temáticas)
2. Para cada sección:
   a. recuperar_contexto(db, sec)   → list[CorpusChunk]
   b. construir_prompt(sec, chunks) → str
   c. gemini.generar_analisis(...)  → str JSON
   d. parsear_seccion(json_str)     → SeccionAnalizada  (con re-intento si inválido)
3. calcular_resumen(secciones)      → ResumenGeneral
4. Persistir en analysis_temp
5. Retornar AnalisisResponse
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

import app.database as database
from app.config import settings
from app.core.exceptions import AnalisisNoEncontradoError, LLMError
from app.models.analysis import AnalysisTemp
from app.repositories.analisis import RepositorioAnalisis
from app.schemas.analysis import (
    AnalisisEstadoResponse,
    AnalisisHistorialItem,
    AnalisisResponse,
    FuenteNormativa,
    Hallazgo,
    HistorialResponse,
    ResumenGeneral,
    SeccionAnalizada,
)
from app.services.llm.base import LLMAdapter
from app.services.llm.gemini_adapter import GeminiAdapter
from app.services.rag_service import recuperar_contexto

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt (Sección 7.1 del prompt maestro)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres un asistente experto en análisis de políticas de privacidad. Tu tarea es ayudar
a jóvenes ciudadanos de Guatemala a comprender el tratamiento de sus datos personales
en plataformas digitales.

PRINCIPIOS DE OPERACIÓN:

1. COBERTURA NORMATIVA: SIEMPRE reporta todos los riesgos que encuentres en el texto,
   independientemente de si el corpus proporcionado los cubre o no. Cuando el contexto
   incluya un fragmento directamente aplicable, cítalo. Cuando el riesgo sea evidente
   pero el corpus no tenga un fragmento específico, reporta el hallazgo indicando
   "Principios generales de protección de datos" como documento fuente. NUNCA omitas
   un riesgo obvio por falta de cita exacta. No inventes nombres de leyes ni artículos
   que no aparezcan en el contexto.

2. DISTINCIÓN JURISDICCIONAL: Guatemala no cuenta con una ley específica e integral
   de protección de datos personales. Cuando una afirmación se base en normativa
   guatemalteca, indícalo claramente. Cuando se base en estándares internacionales
   o regionales (RGPD, LOPDP, Principios OEA, etc.), indica explícitamente que se
   trata de una referencia internacional aplicable como buena práctica, no como ley
   vigente en Guatemala.

3. LENGUAJE ACCESIBLE: Tu audiencia son jóvenes (13-30 años) del municipio de
   San José Acatempa, Jutiapa. Usa lenguaje claro, sin jerga jurídica innecesaria.
   Explica los conceptos técnicos cuando sean indispensables.

4. CLASIFICACIÓN ESTRUCTURADA: Clasifica cada sección de la política según la
   taxonomía OPP-115. Asigna niveles de riesgo (bajo, medio, alto) basados en
   los criterios definidos a continuación.

5. FORMATO DE SALIDA: Responde EXCLUSIVAMENTE en formato JSON válido según el
   esquema definido. No incluyas texto explicativo fuera del JSON.

CRITERIOS DE RIESGO:

ALTO RIESGO (nivel: "alto") — DEBES reportar como alto cualquiera de estos:
- Recopilación de datos biométricos (rostro, huellas, voz, audio pasivo)
- Grabación o captura de audio/video sin finalidad declarada o de forma pasiva
- Datos de salud, registros médicos o datos sensibles sin justificación explícita
- Compartición con terceros no identificados o intermediarios de datos (data brokers)
- Transferencia internacional a países sin leyes de protección de datos equivalentes
- Conservación indefinida o irrenunciable de datos
- Ausencia total de mecanismos para consultar, modificar o eliminar datos
- Recopilación de menores de edad sin verificación de consentimiento parental
- Consentimiento implícito por el simple uso (sin opción real de negarse)
- Cambios unilaterales en la política sin notificación al usuario

RIESGO MEDIO (nivel: "medio"):
- Finalidades amplias o ambiguas ("mejorar servicios", "fines comerciales")
- Plazos de conservación poco claros o sujetos a criterio unilateral
- Mecanismos de ejercicio de derechos engorrosos o sin plazos definidos
- Transferencias internacionales con garantías genéricas sin identificar países

BAJO RIESGO (nivel: "bajo"):
- Lenguaje claro con finalidades específicas y limitadas
- Plazos de conservación definidos
- Mecanismos claros para ejercer derechos con contacto identificado
- Notificación previa de cambios en la política"""

# Fragmentos del corpus a recuperar por sección (5 da mejor cobertura con OpenAI)
_K_FRAGMENTOS = 5
# Tamaño mínimo de sección para considerarla analizable (palabras)
_MIN_PALABRAS_SECCION = 30
# Máximo de secciones a analizar (prototipo: limitar costo/latencia)
_MAX_SECCIONES = 8


# ---------------------------------------------------------------------------
# Segmentación
# ---------------------------------------------------------------------------

def segmentar_politica(texto: str) -> list[str]:
    """Divide la política en secciones temáticas analizables.

    Estrategia: separa por encabezados (líneas en mayúsculas, numeradas o con
    marcadores comunes de sección). Si no se detectan encabezados, cae en
    división por bloques de párrafos de tamaño controlado.
    """
    # Patrón: líneas que parecen títulos de sección
    patron_titulo = re.compile(
        r"^(?:"
        r"\d+[\.\)]\s+"            # "1. " o "1) "
        r"|[IVXLC]+[\.\)]\s+"      # "I. " o "IV) "
        r"|#{1,3}\s+"              # markdown "# " "## "
        r"|[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{4,}$"  # línea todo mayúsculas
        r")",
        re.MULTILINE | re.UNICODE,
    )

    lineas = texto.splitlines()
    secciones: list[str] = []
    bloque_actual: list[str] = []

    for linea in lineas:
        if patron_titulo.match(linea.strip()) and bloque_actual:
            contenido = "\n".join(bloque_actual).strip()
            if len(contenido.split()) >= _MIN_PALABRAS_SECCION:
                secciones.append(contenido)
            bloque_actual = [linea]
        else:
            bloque_actual.append(linea)

    if bloque_actual:
        contenido = "\n".join(bloque_actual).strip()
        if len(contenido.split()) >= _MIN_PALABRAS_SECCION:
            secciones.append(contenido)

    # Fallback: si no se detectaron secciones, dividir en bloques de ~400 palabras
    if not secciones:
        palabras = texto.split()
        tam = 400
        for i in range(0, len(palabras), tam):
            bloque = " ".join(palabras[i : i + tam])
            if len(bloque.split()) >= _MIN_PALABRAS_SECCION:
                secciones.append(bloque)

    return secciones[:_MAX_SECCIONES]


# ---------------------------------------------------------------------------
# Construcción de prompt por sección (Sección 7.2 del prompt maestro)
# ---------------------------------------------------------------------------

def _construir_contexto_normativo(chunks) -> str:
    if not chunks:
        return "No se encontraron fragmentos normativos relevantes para esta sección."

    partes = []
    for i, chunk in enumerate(chunks, 1):
        partes.append(
            f"[Fragmento {i}]\n"
            f"Documento: {chunk.documento_fuente}\n"
            f"Jurisdicción: {chunk.jurisdiccion}\n"
            f"Referencia: {chunk.referencia or 'N/A'}\n"
            f"Contenido: {chunk.texto_original[:600]}"
        )
    return "\n\n".join(partes)


def _construir_prompt_seccion(texto_seccion: str, contexto_normativo: str) -> str:
    return (
        f'SECCIÓN DE LA POLÍTICA A ANALIZAR:\n"""\n{texto_seccion}\n"""\n\n'
        f"FRAGMENTOS NORMATIVOS DE REFERENCIA:\n{contexto_normativo}\n\n"
        "TAREA: Identifica y reporta TODOS los riesgos presentes en la sección anterior.\n"
        "- Si un riesgo tiene respaldo en los fragmentos normativos, cítalo.\n"
        "- Si un riesgo es evidente pero los fragmentos no lo cubren, repórtalo igual\n"
        '  usando "Principios generales de protección de datos" como documento.\n'
        "- NUNCA devuelvas hallazgos vacíos si el texto contiene cláusulas problemáticas.\n\n"
        "Devuelve SOLO el siguiente JSON sin texto adicional:\n\n"
        "{\n"
        '  "categoria_opp115": "<categoría según taxonomía OPP-115>",\n'
        '  "titulo": "<título descriptivo de la sección>",\n'
        '  "texto_original": "<primeras 300 chars de la sección>",\n'
        '  "hallazgos": [\n'
        "    {\n"
        '      "tipo": "riesgo",\n'
        '      "descripcion": "<qué riesgo representa para el usuario en lenguaje claro>",\n'
        '      "nivel": "alto",\n'
        '      "fuentes_normativas": [\n'
        "        {\n"
        '          "documento": "<nombre del documento normativo o Principios generales>",\n'
        '          "referencia": "<artículo o sección>",\n'
        '          "fragmento_relevante": "<texto exacto del fragmento que aplica>"\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}"
    )


# ---------------------------------------------------------------------------
# Parseo y validación de respuesta del LLM
# ---------------------------------------------------------------------------

def _extraer_json(texto: str) -> str:
    """Extrae el bloque JSON de la respuesta aunque venga envuelto en markdown."""
    # Remover bloques ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", texto)
    if match:
        return match.group(1).strip()
    # Intentar encontrar el primer '{' y el último '}'
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio != -1 and fin != -1:
        return texto[inicio : fin + 1]
    return texto.strip()


def _parsear_seccion(json_str: str) -> SeccionAnalizada:
    """Convierte la respuesta JSON del LLM en SeccionAnalizada validada."""
    datos = json.loads(_extraer_json(json_str))

    hallazgos = []
    for h in datos.get("hallazgos", []):
        fuentes = [
            FuenteNormativa(
                documento=f.get("documento", ""),
                referencia=f.get("referencia", ""),
                fragmento_relevante=f.get("fragmento_relevante", ""),
            )
            for f in h.get("fuentes_normativas", [])
        ]
        hallazgos.append(
            Hallazgo(
                tipo=h.get("tipo", "neutral"),
                descripcion=h.get("descripcion", ""),
                nivel=h.get("nivel", "bajo"),
                fuentes_normativas=fuentes,
            )
        )

    return SeccionAnalizada(
        categoria_opp115=datos.get("categoria_opp115", "General"),
        titulo=datos.get("titulo", "Sección sin título"),
        texto_original=datos.get("texto_original", ""),
        hallazgos=hallazgos,
    )


# ---------------------------------------------------------------------------
# Cálculo del resumen general
# ---------------------------------------------------------------------------

_PESO_NIVEL = {"bajo": 1, "medio": 2, "alto": 3}


def _calcular_resumen(secciones: list[SeccionAnalizada]) -> ResumenGeneral:
    todos_hallazgos = [h for s in secciones for h in s.hallazgos]

    if not todos_hallazgos:
        return ResumenGeneral(
            nivel_riesgo_global="bajo",
            puntaje=0,
            comentario_breve="No se identificaron hallazgos en las secciones analizadas.",
        )

    pesos = [_PESO_NIVEL.get(h.nivel, 1) for h in todos_hallazgos]
    promedio = sum(pesos) / len(pesos)
    puntaje = min(100, int((promedio - 1) / 2 * 100))

    alto = sum(1 for h in todos_hallazgos if h.nivel == "alto")
    medio = sum(1 for h in todos_hallazgos if h.nivel == "medio")

    if alto >= 2 or promedio >= 2.5:
        nivel = "alto"
        comentario = (
            f"Esta política presenta {alto} hallazgo(s) de riesgo alto. "
            "Revisa detenidamente las secciones marcadas antes de aceptar."
        )
    elif medio >= 2 or promedio >= 1.5:
        nivel = "medio"
        comentario = (
            f"Se detectaron {medio} hallazgo(s) de riesgo medio. "
            "Algunos aspectos merecen atención, especialmente los usos de tus datos."
        )
    else:
        nivel = "bajo"
        comentario = (
            "La política muestra un nivel de riesgo bajo en los aspectos analizados. "
            "Aun así, te recomendamos revisar los detalles."
        )

    return ResumenGeneral(
        nivel_riesgo_global=nivel,
        puntaje=puntaje,
        comentario_breve=comentario,
    )


def _generar_recomendaciones(secciones: list[SeccionAnalizada]) -> list[str]:
    recomendaciones: list[str] = []
    for seccion in secciones:
        for hallazgo in seccion.hallazgos:
            if hallazgo.nivel in ("alto", "medio"):
                recomendaciones.append(
                    f"En '{seccion.titulo}': {hallazgo.descripcion}"
                )
    if not recomendaciones:
        recomendaciones.append(
            "Esta política parece razonablemente transparente. "
            "Recuerda que siempre puedes solicitar más información al responsable del servicio."
        )
    # Limitar a 5 recomendaciones más relevantes
    return recomendaciones[:5]


# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------

def _crear_adaptador_llm() -> LLMAdapter:
    """Selecciona el adaptador LLM según LLM_PROVIDER en el .env."""
    if settings.llm_provider == "openai":
        from app.services.llm.openai_adapter import OpenAIAdapter
        return OpenAIAdapter(api_key=settings.openai_api_key, model=settings.openai_model)
    return GeminiAdapter(api_key=settings.gemini_api_key, model=settings.gemini_model)


async def crear_analisis(
    db: AsyncSession,
    texto: str,
    user_id: int,
) -> AnalysisTemp:
    """Crea el registro inicial de un análisis (estado 'procesando') y lo comitea.

    El commit explícito (no solo flush) es necesario porque la tarea de fondo
    que sigue (ver ejecutar_analisis_background) usa una sesión de BD distinta
    y solo puede ver filas ya confirmadas por otra conexión.
    """
    registro = AnalysisTemp(
        user_id=user_id,
        texto_original=texto[:2000],  # Guardar solo un extracto
        estado="procesando",
        seccion_actual=0,
    )
    RepositorioAnalisis(db).agregar(registro)
    await db.commit()
    await db.refresh(registro)
    logger.info("Análisis %s creado para usuario %d.", registro.id, user_id)
    return registro


# Referencias a tareas de fondo en curso, para que asyncio no las recolecte a
# medias (ver advertencia de la documentación de asyncio.create_task).
_tareas_en_fondo: set[asyncio.Task] = set()


def lanzar_analisis_en_fondo(analisis_id: int, texto: str) -> None:
    """Programa ejecutar_analisis_background como tarea de fondo del event loop."""
    tarea = asyncio.create_task(ejecutar_analisis_background(analisis_id, texto))
    _tareas_en_fondo.add(tarea)
    tarea.add_done_callback(_tareas_en_fondo.discard)


async def ejecutar_analisis_background(analisis_id: int, texto: str) -> None:
    """Segmenta y analiza la política sección por sección, persistiendo el
    progreso a medida que avanza. Corre en una sesión de BD propia,
    independiente de la sesión del request que la originó (HU-13).
    """
    async with database.AsyncSessionLocal() as db:
        repo = RepositorioAnalisis(db)
        registro: AnalysisTemp | None = None
        try:
            registro = await repo.obtener_por_id(analisis_id)
            if registro is None:
                raise NoResultFound(f"AnalysisTemp {analisis_id} no encontrado")

            llm = _crear_adaptador_llm()
            secciones = segmentar_politica(texto)
            logger.info("Análisis %s: política segmentada en %d secciones.", analisis_id, len(secciones))

            registro.secciones_total = len(secciones)
            await db.commit()

            secciones_analizadas: list[SeccionAnalizada] = []
            for idx, seccion in enumerate(secciones, 1):
                logger.info("Análisis %s: analizando sección %d/%d...", analisis_id, idx, len(secciones))
                try:
                    chunks = await recuperar_contexto(db, seccion, k=_K_FRAGMENTOS)
                    contexto = _construir_contexto_normativo(chunks)
                    # El prompt completo (con esquema JSON y contexto RAG) va como mensaje de usuario
                    user_msg = _construir_prompt_seccion(seccion, contexto)

                    # Intento 1
                    json_str = await llm.generar_analisis(SYSTEM_PROMPT, user_msg, "")
                    try:
                        sec_analizada = _parsear_seccion(json_str)
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning("Sección %d: JSON inválido en intento 1 (%s). Reintentando...", idx, e)
                        # Intento 2: pedir corrección explícita
                        prompt_correccion = (
                            f"Tu respuesta anterior no era JSON válido. "
                            f"Devuelve ÚNICAMENTE el JSON corregido sin texto adicional:\n{json_str[:500]}"
                        )
                        json_str2 = await llm.generar_analisis(SYSTEM_PROMPT, prompt_correccion, "")
                        try:
                            sec_analizada = _parsear_seccion(json_str2)
                        except (json.JSONDecodeError, KeyError, ValueError) as e2:
                            logger.error("Sección %d: JSON inválido tras corrección (%s). Usando fallback.", idx, e2)
                            sec_analizada = _seccion_fallback(seccion, idx)

                    secciones_analizadas.append(sec_analizada)

                except LLMError as exc:
                    logger.error("LLMError en sección %d: %s", idx, exc.detail)
                    secciones_analizadas.append(_seccion_fallback(seccion, idx))
                except Exception as exc:
                    logger.error("Error inesperado en sección %d: %s", idx, exc, exc_info=True)
                    secciones_analizadas.append(_seccion_fallback(seccion, idx))

                registro.seccion_actual = idx
                await db.commit()

            resumen = _calcular_resumen(secciones_analizadas)
            recomendaciones = _generar_recomendaciones(secciones_analizadas)

            respuesta = AnalisisResponse(
                id_analisis=str(analisis_id),
                fecha=datetime.now(timezone.utc),
                resumen_general=resumen,
                secciones_analizadas=secciones_analizadas,
                recomendaciones=recomendaciones,
            )

            registro.resultado = respuesta.model_dump(mode="json")
            registro.estado = "completado"
            await db.commit()
            logger.info(
                "Análisis %s completado. Nivel: %s, puntaje: %d.",
                analisis_id, resumen.nivel_riesgo_global, resumen.puntaje,
            )
        except Exception:
            logger.exception("Análisis %s falló en la tarea de fondo.", analisis_id)
            await db.rollback()
            try:
                if registro is None:
                    registro = await repo.obtener_por_id(analisis_id)
                if registro is not None:
                    registro.estado = "error"
                    await db.commit()
            except Exception:
                logger.exception("No fue posible marcar el análisis %s como error.", analisis_id)


def _seccion_fallback(texto_seccion: str, idx: int) -> SeccionAnalizada:
    """Sección de respaldo cuando el LLM falla o devuelve JSON inválido."""
    return SeccionAnalizada(
        categoria_opp115="General",
        titulo=f"Sección {idx}",
        texto_original=texto_seccion[:500],
        hallazgos=[
            Hallazgo(
                tipo="neutral",
                descripcion="No fue posible analizar esta sección automáticamente.",
                nivel="bajo",
                fuentes_normativas=[],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Recuperación de análisis existente
# ---------------------------------------------------------------------------

async def obtener_analisis(
    db: AsyncSession,
    analisis_id: int,
    user_id: int,
) -> AnalisisResponse:
    """Recupera un análisis completado por su ID, verificando que pertenezca al usuario."""
    registro = await RepositorioAnalisis(db).obtener_por_id_y_usuario(analisis_id, user_id)

    if registro is None or registro.estado != "completado" or registro.resultado is None:
        raise AnalisisNoEncontradoError()

    return AnalisisResponse(**registro.resultado)


async def obtener_estado_analisis(
    db: AsyncSession,
    analisis_id: int,
    user_id: int,
) -> AnalisisEstadoResponse:
    """Devuelve el estado de progreso de un análisis, esté o no completado (HU-13)."""
    registro = await RepositorioAnalisis(db).obtener_por_id_y_usuario(analisis_id, user_id)

    if registro is None:
        raise AnalisisNoEncontradoError()

    return AnalisisEstadoResponse(
        estado=registro.estado,
        seccion_actual=registro.seccion_actual,
        secciones_total=registro.secciones_total,
    )


# ---------------------------------------------------------------------------
# Historial de análisis (HU-14)
# ---------------------------------------------------------------------------

async def listar_historial(
    db: AsyncSession,
    user_id: int,
    page: int,
    page_size: int,
) -> HistorialResponse:
    """Lista paginada de los análisis completados del usuario, más recientes primero."""
    repo = RepositorioAnalisis(db)
    total = await repo.contar_completados_de_usuario(user_id)
    registros = await repo.listar_completados_de_usuario(
        user_id, limit=page_size, offset=(page - 1) * page_size
    )

    items = [
        AnalisisHistorialItem(
            id_analisis=str(registro.id),
            fecha=registro.created_at,
            nivel_riesgo_global=registro.resultado["resumen_general"]["nivel_riesgo_global"],
            puntaje=registro.resultado["resumen_general"]["puntaje"],
            comentario_breve=registro.resultado["resumen_general"]["comentario_breve"],
        )
        for registro in registros
        if registro.resultado is not None
    ]

    return HistorialResponse(items=items, total=total, page=page, page_size=page_size)
