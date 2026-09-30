"""Motor de Análisis: orquesta segmentación, RAG, prompts y llamada al modelo de lenguaje.

Flujo completo por política:
1. segmentar_politica(texto)        → list[str]  (secciones temáticas)
2. Para cada sección:
   a. recuperar_contexto(db, sec)   → list[CorpusChunk]
   b. construir_prompt(sec, chunks) → str
   c. llm.generar_analisis(...)     → str JSON
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
from app.core.exceptions import AnalisisEnCursoError, AnalisisNoEncontradoError, LLMError
from app.models.analysis import AnalysisTemp
from app.repositories.analisis import FiltrosHistorial, RepositorioAnalisis
from app.schemas.analysis import (
    AnalisisEstadoResponse,
    AnalisisHistorialItem,
    AnalisisResponse,
    DistribucionNiveles,
    EstadisticasResponse,
    FuenteNormativa,
    Hallazgo,
    HistorialResponse,
    ResumenGeneral,
    SeccionAnalizada,
    TIPO_TRATAMIENTO_OTRO,
    TIPOS_TRATAMIENTO,
)
from app.services.llm.base import LLMAdapter
from app.services.llm.openai_adapter import OpenAIAdapter
from app.services.rag_service import recuperar_contexto

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt (Sección 7.1 del prompt maestro)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres un asistente experto en análisis de políticas de privacidad. Tu tarea es ayudar
a jóvenes ciudadanos de Guatemala a comprender el tratamiento de sus datos personales
en plataformas digitales.

PRINCIPIOS DE OPERACIÓN:

1. COBERTURA NORMATIVA: SIEMPRE reporta todos los riesgos que encuentres en el texto.
   Respalda cada hallazgo indicando los NÚMEROS de los fragmentos normativos
   proporcionados cuyo contenido lo sustenta (por ejemplo [1, 3]); no copies ni
   redactes el texto de las normas. Indica solo fragmentos que realmente respalden
   el hallazgo. Si ningún fragmento lo respalda, repórtalo igualmente con una lista
   vacía: el sistema lo mostrará como hallazgo sin respaldo en el corpus. NUNCA
   omitas un riesgo obvio por falta de respaldo y NUNCA inventes leyes, artículos
   ni números de fragmento.

2. DISTINCIÓN JURISDICCIONAL: Guatemala no cuenta con una ley específica e integral
   de protección de datos personales. Cuando una afirmación se base en normativa
   guatemalteca, indícalo claramente. Cuando se base en estándares internacionales
   o regionales (RGPD, LOPDP, Principios OEA, etc.), indica explícitamente que se
   trata de una referencia internacional aplicable como buena práctica, no como ley
   vigente en Guatemala. Si un fragmento de Guatemala respalda el hallazgo,
   inclúyelo entre los fragmentos indicados.

3. LENGUAJE ACCESIBLE: Tu audiencia son jóvenes (13-30 años) del municipio de
   San José Acatempa, Jutiapa. Usa lenguaje claro, sin jerga jurídica innecesaria.
   Explica los conceptos técnicos cuando sean indispensables.

4. CLASIFICACIÓN ESTRUCTURADA: Clasifica cada sección de la política según la
   taxonomía OPP-115. Asigna niveles de riesgo (bajo, medio, alto) basados en
   los criterios definidos a continuación.

5. FORMATO DE SALIDA: Responde EXCLUSIVAMENTE en formato JSON válido según el
   esquema definido. No incluyas texto explicativo fuera del JSON.

6. TIPO DE TRATAMIENTO DE DATOS: Clasifica cada hallazgo en UNO SOLO de los
   siguientes tipos, copiando el texto exactamente como aparece:
   - Recopilación de datos personales
   - Uso y finalidad de los datos
   - Transferencia de datos a terceros
   - Tiempo de conservación de los datos
   - Seguridad de los datos
   - Derechos del usuario sobre sus datos
   - Cambios en la política
   - Otro
   Usa "Otro" solo si el hallazgo no corresponde a ninguno de los anteriores.

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
# Fragmentos guatemaltecos que se agregan siempre, aunque no estén entre los 5
# más cercanos: sin ellos el modelo casi nunca puede citar normativa nacional.
_K_GUATEMALA = 2
# Fragmentos que se buscan con la descripción de cada hallazgo que quedó sin
# respaldo, en la segunda pasada (ver _respaldar_hallazgos).
_K_FRAGMENTOS_RESPALDO = 3
# Tamaño mínimo de sección para considerarla analizable (palabras)
_MIN_PALABRAS_SECCION = 30
# Se analiza la política completa: no hay tope de secciones. Las secciones que
# superan _MAX_PALABRAS_SECCION se dividen en bloques de _TAM_BLOQUE palabras,
# el mismo tamaño que se usa para el texto sin encabezados.
_MAX_PALABRAS_SECCION = 700
_TAM_BLOQUE = 500
# Secciones que se envían al modelo al mismo tiempo: acorta el análisis de las
# políticas largas sin acercarse a los límites de solicitudes del proveedor.
_CONCURRENCIA_LLM = 4


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

    # Fallback: si no se detectaron secciones, dividir todo el texto en bloques
    if not secciones:
        return [b for b in _dividir_en_bloques(texto) if len(b.split()) >= _MIN_PALABRAS_SECCION]

    # Las secciones muy largas se dividen para que ningún fragmento llegue al
    # modelo con un tamaño desproporcionado.
    resultado: list[str] = []
    for seccion in secciones:
        if len(seccion.split()) > _MAX_PALABRAS_SECCION:
            resultado.extend(_dividir_en_bloques(seccion))
        else:
            resultado.append(seccion)
    return resultado


def _dividir_en_bloques(texto: str) -> list[str]:
    """Divide el texto en bloques de _TAM_BLOQUE palabras. Si el último bloque
    quedaría demasiado corto, se une al anterior para no perder ese texto."""
    palabras = texto.split()
    bloques = [palabras[i : i + _TAM_BLOQUE] for i in range(0, len(palabras), _TAM_BLOQUE)]
    if len(bloques) > 1 and len(bloques[-1]) < _MIN_PALABRAS_SECCION:
        bloques[-2].extend(bloques.pop())
    return [" ".join(b) for b in bloques]


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
            f"Contenido: {chunk.texto_original[:_LARGO_FRAGMENTO]}"
        )
    return "\n\n".join(partes)


# Caracteres de cada fragmento que ve el modelo y que se muestran en la cita.
_LARGO_FRAGMENTO = 600
_PATRON_ARTICULO = re.compile(r"\bArt(?:[íi]culo|\.)\s*(\d+)", re.IGNORECASE)
_EXTENSIONES_DOCUMENTO = re.compile(r"\.(?:pdf|txt|md)$", re.IGNORECASE)


def _articulos_del_fragmento(texto: str) -> str:
    """Artículos que aparecen en el fragmento ("Artículo 4", "Artículos 3 y 4").
    Vacío si el fragmento no menciona ninguno."""
    numeros = list(dict.fromkeys(_PATRON_ARTICULO.findall(texto)))[:3]
    if not numeros:
        return ""
    if len(numeros) == 1:
        return f"Artículo {numeros[0]}"
    return f"Artículos {', '.join(numeros[:-1])} y {numeros[-1]}"


def _fuente_desde_fragmento(chunk) -> FuenteNormativa:
    """Cita construida con el texto real del corpus: el modelo solo elige el fragmento."""
    texto = " ".join(chunk.texto_original.split())
    extracto = texto if len(texto) <= _LARGO_FRAGMENTO else texto[:_LARGO_FRAGMENTO].rstrip() + "…"
    return FuenteNormativa(
        documento=_EXTENSIONES_DOCUMENTO.sub("", chunk.documento_fuente),
        referencia=_articulos_del_fragmento(extracto),
        fragmento_relevante=extracto,
        jurisdiccion=chunk.jurisdiccion,
    )


def _numeros_de_fragmento(valor, total: int) -> list[int]:
    """Números de fragmento válidos (1..total), sin repetir. Los que no existen se
    descartan: nunca se cita un fragmento que el modelo no recibió."""
    if not isinstance(valor, list):
        raise ValueError(f"'fragmentos' debe ser una lista de números: {valor!r}")
    numeros: list[int] = []
    for elemento in valor:
        try:
            numero = int(elemento)
        except (TypeError, ValueError):
            continue
        if 1 <= numero <= total and numero not in numeros:
            numeros.append(numero)
    return numeros


def _construir_prompt_seccion(texto_seccion: str, contexto_normativo: str) -> str:
    return (
        f'SECCIÓN DE LA POLÍTICA A ANALIZAR:\n"""\n{texto_seccion}\n"""\n\n'
        f"FRAGMENTOS NORMATIVOS DE REFERENCIA:\n{contexto_normativo}\n\n"
        "TAREA: Identifica y reporta TODOS los riesgos presentes en la sección anterior.\n"
        '- En "fragmentos" indica los números de los fragmentos normativos que respaldan\n'
        "  cada hallazgo.\n"
        "- Si un riesgo es evidente pero ningún fragmento lo respalda, repórtalo igual\n"
        '  con "fragmentos": [].\n'
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
        '      "tipo_tratamiento": "<uno de los tipos de tratamiento, copiado exactamente>",\n'
        '      "fragmentos": [<números de los fragmentos que respaldan el hallazgo>]\n'
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


_TIPOS_TRATAMIENTO_NORMALIZADOS = {" ".join(t.split()).casefold(): t for t in TIPOS_TRATAMIENTO}


def _tipo_tratamiento_valido(valor) -> str:
    """Devuelve el texto exacto de la lista cerrada. Tolera solo diferencias de
    mayúsculas o espacios; cualquier otro valor (o su ausencia) es inválido y
    activa el reintento."""
    if isinstance(valor, str):
        canonico = _TIPOS_TRATAMIENTO_NORMALIZADOS.get(" ".join(valor.split()).casefold())
        if canonico:
            return canonico
    raise ValueError(f"tipo_tratamiento fuera de la lista cerrada: {valor!r}")


def _parsear_seccion(json_str: str, chunks=()) -> SeccionAnalizada:
    """Convierte la respuesta JSON del LLM en SeccionAnalizada validada.

    Las fuentes normativas se construyen con los fragmentos recuperados
    (`chunks`) que el modelo indica por número; un hallazgo sin fragmentos
    válidos queda marcado como sin respaldo (RN-06)."""
    datos = json.loads(_extraer_json(json_str))

    hallazgos = []
    for h in datos.get("hallazgos", []):
        numeros = _numeros_de_fragmento(h.get("fragmentos"), len(chunks))
        fuentes = [_fuente_desde_fragmento(chunks[n - 1]) for n in numeros]
        hallazgos.append(
            Hallazgo(
                tipo=h.get("tipo", "neutral"),
                descripcion=h.get("descripcion", ""),
                nivel=h.get("nivel", "bajo"),
                fuentes_normativas=fuentes,
                tipo_tratamiento=_tipo_tratamiento_valido(h.get("tipo_tratamiento")),
                sin_respaldo=not fuentes,
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
    # Los hallazgos sin respaldo en el corpus se muestran, pero no se presentan
    # como fundamentados: no cuentan para el nivel global ni para el puntaje.
    todos_hallazgos = [h for s in secciones for h in s.hallazgos if not h.sin_respaldo]

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
    """Selecciona el adaptador del modelo de lenguaje según LLM_PROVIDER en el .env."""
    if settings.llm_provider == "openai":
        return OpenAIAdapter(api_key=settings.openai_api_key, model=settings.openai_model)
    raise ValueError(f"Proveedor de modelo de lenguaje no soportado: {settings.llm_provider}")


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

            # Las llamadas al modelo corren en paralelo (hasta _CONCURRENCIA_LLM);
            # la sesión de BD no admite uso concurrente, así que la búsqueda en el
            # corpus y el guardado del progreso se serializan con un candado.
            candado_bd = asyncio.Lock()
            limite = asyncio.Semaphore(_CONCURRENCIA_LLM)
            completadas = 0

            async def procesar(idx: int, seccion: str) -> SeccionAnalizada:
                nonlocal completadas
                async with limite:
                    resultado = await _analizar_seccion(llm, db, candado_bd, idx, seccion)
                async with candado_bd:
                    completadas += 1
                    registro.seccion_actual = completadas
                    await db.commit()
                logger.info("Análisis %s: %d/%d secciones analizadas.", analisis_id, completadas, len(secciones))
                return resultado

            # gather conserva el orden original de las secciones.
            secciones_analizadas = list(await asyncio.gather(
                *(procesar(idx, seccion) for idx, seccion in enumerate(secciones, 1))
            ))

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


async def _analizar_seccion(
    llm: LLMAdapter, db: AsyncSession, candado_bd: asyncio.Lock, idx: int, seccion: str
) -> SeccionAnalizada:
    """Analiza una sección: contexto normativo, llamada al modelo y, si la
    respuesta no es válida, un reintento con el motivo del rechazo. Ante un
    error devuelve la sección de respaldo, sin afectar a las demás."""
    try:
        async with candado_bd:
            chunks = await recuperar_contexto(db, seccion, k=_K_FRAGMENTOS, k_guatemala=_K_GUATEMALA)
        contexto = _construir_contexto_normativo(chunks)
        # El prompt completo (con esquema JSON y contexto RAG) va como mensaje de usuario
        user_msg = _construir_prompt_seccion(seccion, contexto)

        # Intento 1
        json_str = await llm.generar_analisis(SYSTEM_PROMPT, user_msg, "")
        try:
            analizada = _parsear_seccion(json_str, chunks)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Sección %d: respuesta inválida en intento 1 (%s). Reintentando...", idx, e)
            # Intento 2: se repite la instrucción completa (sección, contexto y
            # esquema) con el motivo del rechazo, para que el modelo pueda corregirla.
            prompt_correccion = (
                f"{user_msg}\n\n"
                f"Tu respuesta anterior no cumplía el formato requerido ({str(e)[:200]}). "
                "Devuelve ÚNICAMENTE el JSON corregido, sin texto adicional."
            )
            json_str2 = await llm.generar_analisis(SYSTEM_PROMPT, prompt_correccion, "")
            try:
                analizada = _parsear_seccion(json_str2, chunks)
            except (json.JSONDecodeError, KeyError, ValueError) as e2:
                logger.error("Sección %d: respuesta inválida tras corrección (%s). Usando fallback.", idx, e2)
                return _seccion_fallback(seccion, idx)
        return await _respaldar_hallazgos(llm, db, candado_bd, idx, analizada)
    except LLMError as exc:
        logger.error("LLMError en sección %d: %s", idx, exc.detail)
        return _seccion_fallback(seccion, idx)
    except Exception as exc:
        logger.error("Error inesperado en sección %d: %s", idx, exc, exc_info=True)
        return _seccion_fallback(seccion, idx)


SYSTEM_PROMPT_RESPALDO = """Eres un asistente experto en protección de datos personales.
Recibirás hallazgos sobre una política de privacidad y fragmentos numerados de
normativa. Para cada hallazgo, indica los NÚMEROS de los fragmentos cuyo contenido
lo respalda directamente. Si ningún fragmento lo respalda, devuelve una lista vacía.
NUNCA inventes números de fragmento. Responde EXCLUSIVAMENTE en formato JSON válido."""


def _construir_prompt_respaldo(hallazgos: list[Hallazgo], contexto_normativo: str) -> str:
    lista = "\n".join(f"[Hallazgo {i}] {h.descripcion}" for i, h in enumerate(hallazgos, 1))
    return (
        f"HALLAZGOS:\n{lista}\n\n"
        f"FRAGMENTOS NORMATIVOS DE REFERENCIA:\n{contexto_normativo}\n\n"
        "Devuelve SOLO el siguiente JSON sin texto adicional:\n\n"
        "{\n"
        '  "respaldos": [\n'
        '    {"hallazgo": <número del hallazgo>, "fragmentos": [<números de los fragmentos que lo respaldan>]}\n'
        "  ]\n"
        "}"
    )


async def _respaldar_hallazgos(
    llm: LLMAdapter, db: AsyncSession, candado_bd: asyncio.Lock, idx: int, seccion: SeccionAnalizada
) -> SeccionAnalizada:
    """Segunda pasada para los hallazgos que quedaron sin respaldo: busca en el
    corpus con la descripción de cada hallazgo (más precisa que la sección
    completa) y pide al modelo que indique qué fragmentos lo respaldan. Si algo
    falla, la sección se devuelve tal como estaba."""
    pendientes = [h for h in seccion.hallazgos if h.sin_respaldo]
    if not pendientes:
        return seccion
    try:
        fragmentos = []
        ids: set[int] = set()
        async with candado_bd:
            for hallazgo in pendientes:
                for chunk in await recuperar_contexto(db, hallazgo.descripcion, k=_K_FRAGMENTOS_RESPALDO):
                    if chunk.id not in ids:
                        ids.add(chunk.id)
                        fragmentos.append(chunk)
        if not fragmentos:
            return seccion

        prompt = _construir_prompt_respaldo(pendientes, _construir_contexto_normativo(fragmentos))
        datos = json.loads(_extraer_json(await llm.generar_analisis(SYSTEM_PROMPT_RESPALDO, prompt, "")))
        for respaldo in datos.get("respaldos", []):
            try:
                numero_hallazgo = int(respaldo.get("hallazgo"))
                numeros = _numeros_de_fragmento(respaldo.get("fragmentos"), len(fragmentos))
            except (AttributeError, TypeError, ValueError):
                continue
            if not 1 <= numero_hallazgo <= len(pendientes) or not numeros:
                continue
            hallazgo = pendientes[numero_hallazgo - 1]
            hallazgo.fuentes_normativas = [_fuente_desde_fragmento(fragmentos[n - 1]) for n in numeros]
            hallazgo.sin_respaldo = False
    except LLMError as exc:
        logger.warning("Sección %d: sin segunda pasada de respaldo (%s).", idx, exc.detail)
    except Exception as exc:
        logger.warning("Sección %d: segunda pasada de respaldo inválida (%s).", idx, exc)
    return seccion


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
                tipo_tratamiento=TIPO_TRATAMIENTO_OTRO,
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
    filtros: FiltrosHistorial | None = None,
) -> HistorialResponse:
    """Lista paginada de los análisis completados del usuario, más recientes primero,
    con filtros opcionales (siempre dentro de los análisis del propio usuario)."""
    repo = RepositorioAnalisis(db)
    total = await repo.contar_completados_de_usuario(user_id, filtros)
    registros = await repo.listar_completados_de_usuario(
        user_id, limit=page_size, offset=(page - 1) * page_size, filtros=filtros
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


# ---------------------------------------------------------------------------
# Eliminación de análisis (HU-27)
# ---------------------------------------------------------------------------

async def eliminar_analisis(db: AsyncSession, analisis_id: int, user_id: int) -> None:
    """Elimina de forma definitiva un análisis propio. Uno ajeno o inexistente
    responde igual (404), sin revelar si existe. Un análisis en curso no se
    elimina: su tarea de fondo seguiría escribiendo sobre el registro."""
    repo = RepositorioAnalisis(db)
    registro = await repo.obtener_por_id_y_usuario(analisis_id, user_id)
    if registro is None:
        raise AnalisisNoEncontradoError()
    if registro.estado == "procesando":
        raise AnalisisEnCursoError()
    await repo.eliminar(registro)
    logger.info("Análisis %s eliminado por el usuario %d.", analisis_id, user_id)


# ---------------------------------------------------------------------------
# Tiempo de generación del reporte PDF (indicador de la Tabla 1)
# ---------------------------------------------------------------------------

MAX_GENERACIONES_REGISTRADAS = 10


async def registrar_generacion_reporte(
    db: AsyncSession, analisis_id: int, user_id: int, segundos: float
) -> None:
    """Registra en resultado.metadatos_reporte la última generación del PDF, las
    últimas MAX_GENERACIONES_REGISTRADAS mediciones y el total de generaciones."""
    repo = RepositorioAnalisis(db)
    registro = await repo.obtener_por_id_y_usuario(analisis_id, user_id)
    if registro is None or registro.resultado is None:
        return

    anterior = registro.resultado.get("metadatos_reporte") or {}
    medicion = {"fecha": datetime.now(timezone.utc).isoformat(), "segundos": round(segundos, 4)}
    generaciones = [*anterior.get("generaciones", []), medicion][-MAX_GENERACIONES_REGISTRADAS:]
    await repo.guardar_metadatos_reporte(registro, {
        "ultima_generacion_segundos": medicion["segundos"],
        "ultima_generacion_en": medicion["fecha"],
        "total_generaciones": anterior.get("total_generaciones", 0) + 1,
        "generaciones": generaciones,
    })
    logger.info("Reporte PDF del análisis %s generado en %.4f s.", analisis_id, segundos)


async def estadisticas_tiempos_reporte(db: AsyncSession) -> dict:
    """Resumen de los tiempos de generación registrados en todos los análisis
    (las últimas MAX_GENERACIONES_REGISTRADAS mediciones de cada uno)."""
    from app.services.reportes_service import resumir_tiempos

    registros = await RepositorioAnalisis(db).listar_con_metadatos_reporte()
    por_analisis = []
    todas: list[float] = []
    for registro in registros:
        metadatos = registro.resultado["metadatos_reporte"]
        tiempos = [g["segundos"] for g in metadatos.get("generaciones", [])]
        todas.extend(tiempos)
        por_analisis.append({
            "id": registro.id,
            "total_generaciones": metadatos.get("total_generaciones", len(tiempos)),
            "ultima_generacion_segundos": metadatos.get("ultima_generacion_segundos"),
            **resumir_tiempos(tiempos),
        })
    return {
        "analisis_con_reporte": len(registros),
        "total_generaciones": sum(a["total_generaciones"] for a in por_analisis),
        "resumen": resumir_tiempos(todas),
        "por_analisis": por_analisis,
    }


# ---------------------------------------------------------------------------
# Panel estadístico personal (HU-25)
# ---------------------------------------------------------------------------

async def estadisticas_de_usuario(db: AsyncSession, user_id: int) -> EstadisticasResponse:
    """Total de análisis completados del usuario, su distribución por nivel de
    riesgo y la puntuación promedio (ceros si aún no tiene análisis)."""
    filas = await RepositorioAnalisis(db).estadisticas_de_usuario(user_id)
    por_nivel = {nivel: cantidad for nivel, cantidad, _ in filas if nivel in ("bajo", "medio", "alto")}
    total = sum(cantidad for _, cantidad, _ in filas)
    suma_puntajes = sum(suma for _, _, suma in filas)
    return EstadisticasResponse(
        total=total,
        por_nivel=DistribucionNiveles(**por_nivel),
        puntaje_promedio=round(suma_puntajes / total, 1) if total else 0,
    )
