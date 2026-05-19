# Documentación de Arquitectura — PrivApp v1.0

## Visión general

PrivApp sigue una arquitectura de tres capas contenerizada con Docker Compose,
con integración a un servicio externo (Google Gemini API) y un modelo de embeddings
local (Sentence Transformers).

```
Usuario (navegador)
        │
        ▼ HTTP/REST (JSON)
┌──────────────────────────────────┐
│   Frontend React 18 + TypeScript  │
│   Vite · Tailwind CSS · Axios     │
│   Rutas: /login /analizar         │
│          /resultados/:id          │
└──────────────────┬───────────────┘
                   │ REST API
                   ▼
┌──────────────────────────────────┐
│   Backend FastAPI (Python 3.11)   │
│                                   │
│  api/v1/auth      → AuthService   │
│  api/v1/ingesta   → IngestaService│
│  api/v1/analisis  → AnalisisService│
│                        │    │     │
│               RAGService│    │GeminiAdapter
│                        │    │     │
│  utils/embeddings ─────┘    └─────┼── google-generativeai SDK
│  (SentenceTransformer local)      │
└──────────────────┬────────────────┘
                   │ SQL + pgvector
                   ▼
┌──────────────────────────────────┐
│   PostgreSQL 16 + pgvector        │
│   users · analysis_temp           │
│   corpus_chunks (embedding 768D)  │
└──────────────────────────────────┘
```

---

## Decisiones de diseño y justificación

### 1. Patrón Adapter para el LLM

La integración con Gemini está abstraída en la interfaz `LLMAdapter`
([`app/services/llm/base.py`](../backend/app/services/llm/base.py)):

```python
class LLMAdapter(ABC):
    @abstractmethod
    async def generar_analisis(self, system_prompt, texto_seccion, contexto_normativo) -> str: ...
```

`GeminiAdapter` implementa esta interfaz. Cambiar a Claude, GPT-4 u otro proveedor
solo requiere crear una nueva clase sin modificar `AnalisisService`.

**Razón:** El proyecto académico exige demostrar capacidad de diseño extensible.
En la versión final podría evaluarse cambiar de proveedor según costos o disponibilidad.

### 2. PostgreSQL + pgvector como única base de datos

En lugar de una base vectorial separada (Pinecone, Weaviate, Qdrant), se usa la
extensión `pgvector` sobre PostgreSQL. Tanto los datos relacionales (`users`,
`analysis_temp`) como los vectoriales (`corpus_chunks`) conviven en el mismo motor.

**Razón:** Menor complejidad de infraestructura. Menos servicios = menos puntos de
falla. `pgvector` con índice `ivfflat` (listas=100) es suficiente para el volumen
del corpus del prototipo (~500-2 000 chunks).

### 3. Embeddings locales (Sentence Transformers)

El modelo `paraphrase-multilingual-mpnet-base-v2` (~450 MB) se ejecuta dentro
del contenedor del backend como singleton lazy-loaded.

**Razón:** Costo cero por consulta de embeddings. La política analizada nunca sale
del servidor para generar embeddings, lo que protege la privacidad del usuario.
Funciona sin Internet una vez descargado.

### 4. RAG (Retrieval-Augmented Generation)

El `AnalisisService` no pasa el texto completo a Gemini de una vez. Para cada sección:
1. Genera el embedding de la sección (768D).
2. Busca los top-5 fragmentos normativos más similares en `corpus_chunks` (coseno).
3. Construye el prompt con la sección + el contexto normativo estructurado.

**Razón:** Garantiza que el análisis esté fundamentado en fuentes verificables.
El system prompt instruye a Gemini a citar exclusivamente los fragmentos entregados,
no inventar referencias. Esto es un requisito académico de honestidad en el análisis.

### 5. System prompt OPP-115

El system prompt implementa la taxonomía OPP-115 para clasificar secciones
(First Party Collection, Data Retention, User Choice, etc.) y los criterios
de riesgo definidos en el diseño del proyecto (Sección 7.1 del prompt maestro).

**Razón:** La taxonomía OPP-115 es el estándar académico más citado para análisis
automatizado de políticas de privacidad, lo que da validez metodológica al proyecto.

### 6. Validación JSON con re-intento

Si Gemini devuelve JSON malformado, el servicio:
1. Intenta extraer el bloque JSON (incluso si viene envuelto en markdown ` ```json ```).
2. Si falla, solicita a Gemini una corrección explícita.
3. Si falla de nuevo, usa una sección de fallback ("No fue posible analizar").

**Razón:** Robustez ante comportamiento no determinista del LLM. En producción,
los modelos de lenguaje ocasionalmente añaden texto fuera del JSON solicitado.

### 7. JWT sin refresh tokens (prototipo)

Tokens con expiración de 24 horas, sin refresh. Invalidación client-side en logout.

**Razón:** Suficiente para el alcance del prototipo. Los refresh tokens se implementarán
en Proyecto de Graduación II.

---

## Flujo completo de una solicitud de análisis

```
Usuario
  │ POST /api/ingesta/texto  {texto: "..."}
  ▼
IngestaService.procesar_texto_directo(texto)
  │ limpiar_texto() → validar longitud (200–50 000 chars)
  │ return texto_limpio
  ▼
POST /api/analisis/iniciar  {texto: texto_limpio}
  ▼
AnalisisService.iniciar_analisis(texto, user_id)
  │ AnalysisTemp(estado="procesando") → db.flush()
  │
  │ segmentar_politica(texto)
  │   ├── detectar encabezados (numerados, markdown, MAYÚSCULAS)
  │   └── fallback: bloques de 400 palabras
  │   → list[str]  (máx. 8 secciones)
  │
  │ Para cada sección:
  │   │ recuperar_contexto(db, seccion, k=5)
  │   │   encode(seccion) → vector 768D
  │   │   SELECT ... ORDER BY embedding <=> CAST(:vec AS vector) LIMIT 5
  │   │   → list[CorpusChunk]
  │   │
  │   │ _construir_contexto_normativo(chunks) → str
  │   │
  │   │ GeminiAdapter.generar_analisis(SYSTEM_PROMPT, seccion, contexto)
  │   │   generate_content_async()  (hasta 3 reintentos con backoff)
  │   │   → str (JSON o texto con JSON)
  │   │
  │   │ _parsear_seccion(json_str)
  │   │   _extraer_json()  ← maneja bloques markdown
  │   │   SeccionAnalizada(**datos)
  │   │   → SeccionAnalizada | fallback si falla
  │
  │ _calcular_resumen(secciones)
  │   pesos = [bajo=1, medio=2, alto=3]
  │   puntaje = (promedio - 1) / 2 * 100
  │   → ResumenGeneral
  │
  │ _generar_recomendaciones(secciones)  → list[str] (máx. 5)
  │
  │ AnalysisTemp.resultado = respuesta.model_dump()
  │ AnalysisTemp.estado = "completado"
  │ db.flush()
  │
  └─→ AnalisisResponse  (HTTP 201)
  ▼
Frontend: navigate("/resultados/{id}", state: {resultado})
  │ Resultados.tsx usa el state directamente (sin re-fetch)
  └─→ PanelResultados con TarjetaSeccion, CitaNormativa, ListaRecomendaciones
```

---

## Estructura de módulos del backend

```
app/
├── main.py              # FastAPI app, CORS, SlowAPI, routers
├── config.py            # Pydantic Settings (env vars)
├── database.py          # Async engine, AsyncSessionLocal, get_db()
├── core/
│   ├── security.py      # JWT (python-jose) + bcrypt (passlib)
│   ├── exceptions.py    # HTTPExceptions personalizadas con status codes
│   └── limiter.py       # slowapi Limiter (rate limiting por IP)
├── models/
│   ├── user.py          # User (id, nombre, email, hashed_password)
│   ├── corpus.py        # CorpusChunk (texto, embedding vector(768), metadatos)
│   └── analysis.py      # AnalysisTemp (user_id FK, resultado JSONB, estado)
├── schemas/
│   ├── auth.py          # RegisterRequest (con validador de contraseña), TokenResponse
│   ├── analysis.py      # AnalisisResponse, SeccionAnalizada, Hallazgo, FuenteNormativa
│   ├── ingesta.py       # IngestaResponse
│   └── analisis_request.py  # IniciarAnalisisRequest
├── api/v1/
│   ├── auth.py          # /register /login /logout /me
│   ├── ingesta.py       # /texto /url
│   └── analisis.py      # /iniciar /{id}
├── services/
│   ├── auth_service.py  # register_user, authenticate_user
│   ├── ingesta_service.py  # limpiar_texto, procesar_texto_directo, extraer_texto_url
│   ├── rag_service.py   # recuperar_contexto (pgvector), contar_chunks
│   ├── analisis_service.py  # segmentar_politica, iniciar_analisis, obtener_analisis
│   └── llm/
│       ├── base.py      # LLMAdapter (ABC)
│       └── gemini_adapter.py  # GeminiAdapter (tenacity retries)
└── utils/
    ├── chunking.py      # chunk_texto (solapamiento 50 palabras)
    ├── embeddings.py    # SentenceTransformer singleton, encode/encode_batch
    └── pdf_extractor.py # pdfplumber → pypdf fallback
```

---

## Cambios respecto al marco teórico original

| Aspecto | Diseño original | Implementación final | Justificación |
|---|---|---|---|
| Motor de análisis | Palabras clave + regex | RAG + LLM | Precisión y explicabilidad significativamente superiores |
| Base vectorial | Pinecone (separada) | pgvector en PostgreSQL | Menor complejidad, suficiente para el volumen |
| Embeddings | API externa | Sentence Transformers local | Costo cero + privacidad del texto |
| Validación LLM | No prevista | Re-intento con corrección explícita | Robustez ante respuestas malformadas |
| Segmentación | No especificada | Detección de encabezados + fallback a bloques | Balance entre fidelidad semántica y velocidad |

Estos cambios están documentados en [`CHANGELOG.md`](../CHANGELOG.md) en la sección
"Decisiones técnicas documentadas" y representan mejoras técnicas respecto al diseño
inicial, justificadas para transparencia académica.
