# Documentación de Arquitectura — PrivApp

## Visión general

PrivApp sigue una arquitectura de tres capas (frontend, backend, base de datos)
contenerizada con Docker Compose, con integración a un servicio externo (Google Gemini API).

```
Usuario → React Frontend → FastAPI Backend → PostgreSQL + pgvector
                                         ↕
                                   Google Gemini API (externo)
                                   Sentence Transformers (local)
```

## Decisiones de diseño

### 1. Patrón Adapter para el LLM

La integración con Gemini se abstrae en la interfaz `LLMAdapter` (`app/services/llm/base.py`).
El `GeminiAdapter` implementa esta interfaz. Cambiar de Gemini a Claude u otro proveedor
solo requiere crear una nueva clase que implemente `LLMAdapter`, sin modificar el
`AnalisisService`.

**Razón:** El proyecto académico exige demostrar capacidad de diseño extensible. En la
versión final podría evaluarse cambiar de proveedor de LLM según costos o disponibilidad.

### 2. PostgreSQL + pgvector como única base de datos

En lugar de usar una base de datos vectorial separada (Pinecone, Weaviate, Qdrant),
se utiliza la extensión `pgvector` sobre PostgreSQL. Esto permite manejar datos
relacionales y vectoriales en un único motor.

**Razón:** Simplicidad de la infraestructura del prototipo. Menos servicios = menos
puntos de falla. `pgvector` con índice `ivfflat` es suficiente para el volumen del corpus.

### 3. Embeddings locales (Sentence Transformers)

El modelo `paraphrase-multilingual-mpnet-base-v2` se ejecuta dentro del contenedor
del backend, sin llamadas a APIs externas.

**Razón:** Costo cero por consulta de embeddings, privacidad del texto procesado
(la política analizada nunca sale del servidor para generar embeddings), y funcionamiento
sin conexión a Internet una vez descargado el modelo.

### 4. RAG (Retrieval-Augmented Generation)

Cada sección de la política se convierte a embedding, se buscan los 5 fragmentos
normativos más similares en el corpus, y estos se incluyen en el prompt a Gemini.

**Razón:** Garantiza que el análisis esté fundamentado en fuentes verificables.
El sistema puede citar exactamente qué artículo o principio respalda cada hallazgo,
lo que es un requisito académico de honestidad en el análisis.

### 5. JWT sin refresh tokens (prototipo)

La autenticación usa JWT con expiración de 24 horas. No se implementan refresh tokens
en el prototipo.

**Razón:** Suficiente para el alcance del prototipo. Los refresh tokens se implementarán
en la versión final.

## Flujo completo de análisis

1. Usuario autenticado envía texto de política al endpoint `/api/ingesta/texto`.
2. El backend valida el texto (200–50,000 caracteres).
3. `AnalisisService` segmenta la política en secciones por párrafos/temas.
4. Para cada sección: `EmbeddingService.encode(seccion)` → vector de 768 dimensiones.
5. `RAGService.recuperar_contexto(vector, k=5)` → top-5 fragmentos normativos.
6. `GeminiAdapter.generar_analisis(system_prompt, seccion, contexto)` → JSON.
7. La respuesta JSON se valida con Pydantic; si falla, se reintenta (máx. 3 veces).
8. El resultado se almacena en `analysis_temp` y se devuelve al frontend.
9. El frontend renderiza el Panel de Visualización.

## Estructura de módulos del backend

```
app/
├── main.py           # Punto de entrada FastAPI, CORS, middleware
├── config.py         # Variables de entorno (Pydantic Settings)
├── database.py       # Motor async SQLAlchemy, sesiones
├── core/
│   ├── security.py   # JWT + bcrypt
│   └── exceptions.py # HTTPExceptions personalizadas
├── models/           # Entidades SQLAlchemy
├── schemas/          # Validación Pydantic (DTOs)
├── api/v1/           # Routers FastAPI por módulo
├── services/         # Lógica de negocio
│   └── llm/          # Adaptadores LLM (interfaz + Gemini)
└── utils/            # Chunking, embeddings, extracción PDF
```

## Cambios respecto al marco teórico original

| Aspecto | Planteamiento original | Decisión final |
|---|---|---|
| Análisis de texto | Palabras clave + regex | RAG + LLM (mayor precisión y explicabilidad) |
| Base vectorial | Separada (Pinecone) | pgvector integrado en PostgreSQL (menor complejidad) |
| Embeddings | API externa | Modelo local (ahorro de costos + privacidad) |

Estos cambios están justificados en `CHANGELOG.md` y representan mejoras técnicas
respecto al diseño inicial, documentadas para transparencia académica.
