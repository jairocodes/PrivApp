# Changelog

Todos los cambios notables de este proyecto están documentados en este archivo.  
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).

---

## [1.0.0-prototipo] — 2026-05-18 — Release: Prototipo funcional completo

### Summary
Prototipo funcional demostrativo completado para el Proyecto de Graduación I.
El sistema permite a un usuario registrado analizar una política de privacidad
(por texto o URL) y obtener un análisis estructurado con niveles de riesgo,
hallazgos con citas normativas y recomendaciones accionables.

### Included
- Sprints 0 al 5 completos (ver entradas individuales abajo).
- 65+ tests automatizados en el backend.
- Documentación completa: instalación, API, arquitectura, guía del evaluador.

---

## [0.5.0] — 2026-05-18 — Sprint 5: Panel de Visualización

### Added
- `IndicadorSemaforo`: props `size` (sm/md/lg) y `mostrarTexto` para modo banner
  con fondo de color, descripción contextual y dot ring por nivel.
- `CitaNormativa`: badge de jurisdicción (Guatemala azul, Internacional morado,
  Estándar técnico gris), inferencia automática por nombre de documento,
  nota aclaratoria para referencias internacionales.
- `TarjetaSeccion`: tarjeta expandible/colapsable con nivel máximo en cabecera,
  hallazgos con ícono por tipo (riesgo/transparencia/neutral), chips de nivel,
  extracto del texto analizado y citas normativas anidadas.
- `ListaRecomendaciones`: lista numerada con ícono Lightbulb, leading-relaxed.
- `Resultados.tsx` completo mobile-first: puntaje circular 0-100, resumen ejecutivo
  con stats rápidas (secciones / hallazgos críticos / recomendaciones), secciones
  con primera expandida por defecto, aviso académico de limitación legal, botón
  "Analizar otra política", spinner de carga animado, estado de error con ícono.

### Changed
- `Resultados.tsx` reemplaza la vista básica de Sprint 4 con panel completo.

---

## [0.4.0] — 2026-05-18 — Sprint 4: Motor de Análisis

### Added
- `analisis_service.py`: orquestador completo del motor de análisis.
  - Segmentación de política por encabezados (numerados, markdown, mayúsculas)
    con fallback a bloques de 400 palabras. Máximo 8 secciones por análisis.
  - System prompt OPP-115 completo (Sección 7.1 del diseño) con criterios de riesgo
    ALTO/MEDIO/BAJO, distinción jurisdiccional Guatemala vs internacional.
  - Construcción de contexto normativo estructurado con los 5 fragmentos más relevantes.
  - Parseo JSON con extracción desde bloques markdown (` ```json ``` `).
  - Re-intento automático con corrección explícita si el LLM devuelve JSON inválido.
  - Sección de fallback ("No fue posible analizar") si el LLM falla definitivamente.
  - Cálculo de resumen: puntaje 0-100 ponderado, nivel global bajo/medio/alto.
  - Persistencia del resultado en `analysis_temp` con estado "procesando"→"completado".
- `api/v1/analisis.py`: `POST /api/analisis/iniciar` (5/min) y `GET /api/analisis/{id}`,
  ambos protegidos con JWT.
- `schemas/analisis_request.py`: `IniciarAnalisisRequest` (min 200, max 50 000 chars).
- `migrations/versions/0003_analysis_temp_table.py`: tabla `analysis_temp` con índices
  sobre `user_id` y `estado`.
- `IngestaForm.tsx` actualizado: flujo completo ingesta→análisis en dos fases con
  mensajes de estado diferenciados ("Procesando texto..." / "Analizando con IA...").
- `api/analisis.ts` y `hooks/useAnalisis.ts`: cliente tipado e inicialización de estado.
- `Resultados.tsx` básico: muestra semáforo, secciones, hallazgos y recomendaciones
  (completado en Sprint 5).

### Changed
- `conftest.py`: crea tabla `analysis_temp` en SQLite para tests de integración.
- `main.py`: versión 0.4.0, router de análisis registrado.

### Tests
- 15 tests: segmentación, parseo JSON, cálculo de resumen, endpoints de integración
  con Gemini mockeado.

---

## [0.3.0] — 2026-05-18 — Sprint 3: Ingesta y adaptador Gemini

### Added
- `GeminiAdapter`: integración completa con `google-generativeai` SDK.
  - `system_instruction` en instanciación del modelo.
  - `generate_content_async()` para llamadas no bloqueantes.
  - Reintentos exponenciales con `tenacity` (máx. 3, espera 2-10 s).
  - Distinción entre errores transitorios (reintentables) y permanentes (API key inválida).
- `ingesta_service.py`: `limpiar_texto` (normalización unicode NFC, colapso de espacios
  y saltos), `procesar_texto_directo` y `extraer_texto_url`.
  - Extracción HTML con `beautifulsoup4`: limpia `<script>`, `<style>`, `<nav>`,
    prioriza `<main>` o `<article>`, fallback a `<body>`.
  - Manejo de errores HTTP (timeout, 404, contenido no HTML).
- `api/v1/ingesta.py`: `POST /api/ingesta/texto` (20/min) y `POST /api/ingesta/url`
  (10/min), protegidos con JWT.
- `schemas/ingesta.py`: `IngestaResponse` con `texto_procesado`, `palabras`, `fuente`.
- `IngestaForm.tsx`: pestañas texto/URL, contador de caracteres con color dinámico,
  validación frontend, feedback de carga.

### Changed
- `main.py`: versión 0.3.0, router de ingesta registrado.

### Tests
- 13 tests: limpieza de texto, servicio con mocks HTTP, endpoints de integración.

---

## [0.2.0] — 2026-05-18 — Sprint 2: Corpus normativo y arquitectura RAG

### Added
- `models/corpus.py`: modelo `CorpusChunk` con campo `embedding vector(768)` (pgvector).
- `migrations/versions/0002_corpus_chunks_table.py`: tabla `corpus_chunks` con índice
  `ivfflat` para búsqueda por coseno y extensión `pgvector`.
- `utils/pdf_extractor.py`: extracción con `pdfplumber` (primario) y `pypdf` (fallback).
- `utils/chunking.py`: chunking semántico por párrafos con solapamiento de 50 palabras,
  tamaño 300-500 palabras, split forzado para párrafos gigantes.
- `utils/embeddings.py`: singleton de `SentenceTransformer` con modelo
  `paraphrase-multilingual-mpnet-base-v2`, `encode()` y `encode_batch()`.
- `scripts/cargar_corpus.py`: carga idempotente (hash MD5 por chunk), inferencia de
  jurisdicción por carpeta, categoría por keywords del nombre de archivo, estadísticas
  al finalizar, flag `--limpiar` con confirmación.
- `services/rag_service.py`: `recuperar_contexto()` con consulta pgvector `<=>`,
  filtros opcionales por jurisdicción y categoría, `contar_chunks()`.
- `corpus_normativo/estandares_tecnicos/tosdr_metodologia.md`: referencia metodológica.
- `corpus_normativo/README.md`: instrucciones para colocar los PDFs.

### Tests
- 22 tests: chunking, metadatos de corpus, extractor PDF, embeddings con mock,
  RAG service con mock de DB.

---

## [0.1.0] — 2026-05-18 — Sprint 1: Módulo de Autenticación

### Added
- `models/user.py`: modelo `User` (id, nombre, email único, hashed_password, is_active,
  created_at).
- `migrations/versions/0001_create_users_table.py`: tabla `users` con índice en `email`.
- `core/security.py`: `hash_password`, `verify_password`, `create_access_token`,
  `decode_access_token` (JWT con expiración configurable).
- `core/exceptions.py`: excepciones personalizadas con HTTP status codes apropiados
  (CredencialesInvalidasError, UsuarioNoEncontradoError, UsuarioYaExisteError,
  TokenInvalidoError, TextoDemasiadoCortoError, TextoDemasiadoLargoError,
  ExtraccionURLError, LLMError, AnalisisNoEncontradoError).
- `core/limiter.py`: instancia de `slowapi` para rate limiting por IP.
- `services/auth_service.py`: `register_user`, `authenticate_user`,
  `get_user_by_email`, `get_user_by_id`.
- `api/deps.py`: dependencias `get_current_user_id` y `get_current_user`.
- `api/v1/auth.py`: endpoints `POST /register` (10/min), `POST /login` (5/min),
  `POST /logout`, `GET /me`.
- `schemas/auth.py`: `RegisterRequest` con validación de fortaleza de contraseña
  (mínimo 8 chars, mayúscula, número), `LoginRequest`, `TokenResponse`, `UserResponse`.
- `AuthContext.tsx`: carga el usuario al montar, provee `login`, `register`, `logout`.
- `LoginForm.tsx`: formulario con email/contraseña, manejo de errores, navegación.
- `RegisterForm.tsx`: formulario con nombre/email/contraseña/confirmación, validación.
- `Navbar.tsx`: marca PrivApp + botón logout con ícono.
- `ProtectedRoute.tsx`: redirige a `/login` si no autenticado.
- Rate limiting middleware con `SlowAPIMiddleware`.

### Tests
- 15 tests: healthcheck, registro, login, rutas protegidas.

---

## [0.0.1] — 2026-05-18 — Sprint 0: Configuración inicial

### Added
- Estructura completa del repositorio según la arquitectura del diseño.
- `docker-compose.yml` con servicios: PostgreSQL 16 + pgvector, backend FastAPI,
  frontend React.
- Dockerfiles para backend (Python 3.11 slim) y frontend (Node 20 slim).
- `postgres/init.sql`: extensiones `vector` y `uuid-ossp`, tabla `corpus_chunks`.
- Skeleton de FastAPI con endpoint `GET /health`.
- Skeleton de React 18 + Vite + Tailwind CSS con estructura de rutas y contexto.
- Definición completa de modelos SQLAlchemy: `User`, `CorpusChunk`, `AnalysisTemp`.
- Schemas Pydantic v2, interfaz `LLMAdapter` (patrón Adapter), placeholders de servicios.
- `.gitignore`, `.env.example`, `LICENSE` (MIT), `README.md`, `CONTRIBUTING.md`.
- Documentación inicial en `docs/`.

---

## Decisiones técnicas documentadas

| Decisión | Planteamiento original | Implementación final | Justificación |
|---|---|---|---|
| Motor de análisis | Palabras clave + regex | RAG + Gemini | Mayor precisión y explicabilidad |
| Base vectorial | Pinecone (separada) | pgvector en PostgreSQL | Menos infraestructura, suficiente para el volumen |
| Embeddings | API externa | Sentence Transformers local | Costo cero + privacidad del texto |
| Validación JSON del LLM | No prevista | Re-intento con corrección explícita | Robustez ante respuestas mal formadas |
