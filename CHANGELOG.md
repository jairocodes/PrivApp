# Changelog

Todos los cambios notables de este proyecto están documentados en este archivo.  
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).

---

## [Sin publicar] — Proyecto de Graduación II

Versión completa del sistema para el Capítulo VI. Se publicará al integrar
`develop` en `main` con el despliegue en Railway.

### Added
- **Cuentas y sesiones:** rol usuario/administrador validado con el rol vigente en la
  base de datos; fecha de emisión e identificador (`jti`) en los tokens; cierre de
  sesión con revocación en Redis; invalidación de todas las sesiones al cambiar la
  contraseña o desactivar una cuenta (`sessions_valid_from`).
- **Aviso de privacidad:** página pública, aceptación obligatoria al registrarse
  (`privacy_accepted_at`) y declaración obligatoria de mayoría de edad o de
  consentimiento de la madre, el padre o la persona encargada (`age_declaration_at`).
- **Perfil:** edición del nombre, cambio de contraseña y eliminación definitiva de la
  propia cuenta con todos sus análisis.
- **Administración:** listado y búsqueda de usuarios (sin distinguir acentos),
  activación y desactivación de cuentas; listado, carga (PDF/TXT) y activación o
  desactivación de documentos del corpus normativo. Script `promover_admin.py`.
- **Ingesta:** carga de archivos PDF o TXT de hasta 5 MB procesados en memoria,
  regla única de longitud (200 caracteres y 40 palabras, máximo 300,000, con un
  mensaje que dice cuánto mide el texto y qué hacer si lo supera) y vista
  previa obligatoria antes de analizar.
- **Análisis:** progreso en segundo plano; clasificación de cada hallazgo en uno de
  ocho tipos de tratamiento de datos; análisis de la política completa, con hasta
  cuatro secciones en paralelo; citas normativas construidas con el texto real de los
  fragmentos del corpus; normativa guatemalteca incluida en el contexto de cada
  sección; segunda búsqueda de respaldo con la descripción de cada hallazgo;
  hallazgos sin respaldo marcados, que no suman a la puntuación; recomendaciones
  prácticas redactadas a partir de los riesgos encontrados.
- **Resultados:** filtro de hallazgos por nivel y jurisdicción, ayuda contextual del
  glosario y eliminación del análisis desde su detalle.
- **Historial:** filtros por nivel, rango de fechas y texto (sin distinguir acentos) y
  eliminación definitiva con confirmación.
- **Panel estadístico** personal con gráfico de distribución por nivel (recharts,
  cargado de forma diferida).
- **Glosario** público de 22 términos con búsqueda sin acentos.
- **Reportes:** tipo de tratamiento y hallazgos sin respaldo en el PDF; registro del
  tiempo de generación y script `tiempos_reporte.py`.
- **Pruebas:** Vitest con jsdom en el cliente; pruebas de integración contra
  PostgreSQL con pgvector (`PRIVAPP_TEST_PG_URL`).
- **Consistencia del análisis:** el modelo elige el código del criterio de la rúbrica
  (A1–A10, M1–M5, B1–B4) y el servidor deriva el nivel y el tipo del hallazgo;
  temperatura 0, semilla fija y salidas estructuradas estrictas; un último intento
  por sección ante errores transitorios; reutilización del resultado de un texto
  idéntico analizado con la misma configuración (`analysis_temp.text_hash`);
  configuración de cada análisis en `resultado.metadatos_analisis`; script
  `medir_consistencia.py`.
- **Interfaz:** tokens de color con modo claro y oscuro (preferencia guardada; por
  defecto la del dispositivo) e interruptor sol/luna; fuente Figtree servida desde
  el propio sitio; barra superior y pestañas inferiores en el celular con la sección
  actual marcada; enlace para saltar al contenido; componentes comunes (avisos,
  carga, estado vacío, encabezado, insignias, paginación y campos); diálogo de
  confirmación con Headless UI (foco retenido); favicon.
- **Pantalla de resultados rediseñada:** medidor semicircular con franjas de
  referencia, "¿Por qué este resultado?" con las cláusulas que cuentan y la regla del
  nivel, fichas de "Qué hace con tus datos" por tipo de tratamiento que filtran la
  lista, "Por qué" de cada hallazgo según su criterio, normas desplegables,
  recomendaciones como tarjetas de acción y dos columnas en escritorio.
- **Validación del contenido (RN-18):** cada vía de ingesta y el inicio del análisis
  detectan si el texto es una política de privacidad con vocabulario por temas,
  semejanza semántica (embeddings del corpus) y la voz del responsable; los textos que
  claramente no lo son se rechazan, y los dudosos exigen confirmación en la vista
  previa. Un análisis en el que casi ninguna sección trata de datos personales termina
  sin puntuación (`motivo: no_es_politica`). Script `evaluar_deteccion.py`. El modelo de
  embeddings se carga desde la caché local sin consultar en línea.
- Migraciones 0005 a 0011.

### Changed
- OpenAI es el único proveedor del modelo de lenguaje (`LLM_PROVIDER=openai`).
- Búsqueda exacta en el corpus normativo: se elimina el índice aproximado ivfflat.
- "Puntaje de riesgo" pasa a llamarse "Puntuación de riesgo".
- Arranque con `lifespan`; `--reload` solo en desarrollo; cabeceras de reenvío del
  proxy de Railway.
- Imagen de producción del frontend: los archivos estáticos se construyen con
  `VITE_API_URL` y los sirve nginx; el servidor de Vite queda solo para desarrollo.
- Repositorios separados para usuarios, análisis y corpus.

### Removed
- Adaptador de Gemini.
- Tope de ocho secciones por análisis.
- La cita genérica "Principios generales de protección de datos".

### Fixed
- Jurisdicción del Decreto 57-2008 (Guatemala) y de ToS;DR (estándar técnico).
- Mensaje claro al superar el límite de solicitudes.
- Rechazo temprano de archivos demasiado grandes.
- Carga del corpus solo desde las carpetas de jurisdicción.
- Política de reintentos del adaptador de OpenAI.

### Security
- Los registros del servidor no guardan correos, direcciones IP, nombres de archivos
  cargados ni direcciones web completas; producción arranca sin registro de acceso.

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
