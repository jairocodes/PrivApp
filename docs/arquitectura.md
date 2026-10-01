# Documentación de Arquitectura — PrivApp v1.0

## Visión general

PrivApp sigue una arquitectura de tres capas contenerizada con Docker Compose,
con integración a un servicio externo (OpenAI, modelo `gpt-4o-mini`), un modelo de
embeddings local (Sentence Transformers) y Redis para la revocación de sesiones.

```
Usuario (navegador)
        │
        ▼ HTTP/REST (JSON)
┌───────────────────────────────────────────┐
│   Frontend React 18 + TypeScript           │
│   Vite · Tailwind CSS · Axios · Recharts   │
│   Rutas públicas: /login /registro         │
│     /aviso-privacidad /glosario            │
│   Rutas protegidas: /dashboard /analizar   │
│     /resultados/:id /historial /perfil     │
│   Rutas de administración: /admin          │
│     /admin/usuarios /admin/corpus          │
└──────────────────────┬────────────────────┘
                       │ REST API (Bearer JWT)
                       ▼
┌───────────────────────────────────────────┐
│   Backend FastAPI (Python 3.11)            │
│                                            │
│  api/v1/auth      → auth_service           │
│  api/v1/ingesta   → ingesta_service        │
│  api/v1/analisis  → analisis_service       │
│                     reportes_service (PDF) │
│  api/v1/admin     → admin_service          │
│                     corpus_service         │
│                                            │
│  analisis_service ─┬─ rag_service          │
│                    └─ LLMAdapter           │
│                        └─ OpenAIAdapter ───┼── SDK openai
│  rag_service ── utils/embeddings           │
│                 (SentenceTransformer local)│
│  repositories/ (acceso a datos)            │
└─────────┬──────────────────────┬──────────┘
          │ SQL + pgvector       │ jti revocados
          ▼                      ▼
┌─────────────────────────┐ ┌──────────────┐
│ PostgreSQL 16 + pgvector │ │  Redis 7     │
│ users · analysis_temp    │ │  revoked_jti │
│ corpus_chunks (768D)     │ └──────────────┘
└─────────────────────────┘
```

---

## Capas del backend

| Capa | Ubicación | Responsabilidad |
|---|---|---|
| Rutas | `app/api/v1/` | Validar la solicitud (esquemas Pydantic), aplicar los límites de solicitudes y la autorización, delegar al servicio |
| Dependencias | `app/api/deps.py` | Decodificar el token, comprobar revocación y `sessions_valid_from`, cargar el usuario vigente, exigir el rol administrador |
| Servicios | `app/services/` | Reglas del negocio: autenticación, ingesta, análisis, reportes, corpus y administración |
| Repositorios | `app/repositories/` | Única capa que construye consultas SQL |
| Modelos | `app/models/` | Tablas SQLAlchemy |
| Núcleo | `app/core/` | Seguridad (JWT, bcrypt), revocación en Redis, excepciones, limitador, registros, rechazo temprano de cargas grandes |

---

## Decisiones de diseño y justificación

### 1. Patrón Adapter y fábrica para el modelo de lenguaje

La integración con el modelo está abstraída en la interfaz `LLMAdapter`
([`app/services/llm/base.py`](../backend/app/services/llm/base.py)):

```python
class LLMAdapter(ABC):
    @abstractmethod
    async def generar_analisis(self, system_prompt, texto_seccion, contexto_normativo) -> str: ...
```

`OpenAIAdapter` ([`openai_adapter.py`](../backend/app/services/llm/openai_adapter.py))
implementa esta interfaz con el SDK `openai`: temperatura 0.2, respuesta en modo JSON
(`response_format={"type": "json_object"}`) y hasta 3 intentos con espera exponencial
(tenacity) ante límites de solicitudes, errores de red o errores 5xx. Los errores no
reintentables se convierten en `LLMError`.

El adaptador se obtiene de la fábrica `_crear_adaptador_llm()` de `analisis_service`,
que lo elige según la variable `LLM_PROVIDER`. Hoy el único valor soportado es
`openai`; cualquier otro produce un error explícito. Agregar otro proveedor solo
requiere una nueva clase que implemente `LLMAdapter` y una rama en la fábrica, sin
modificar el resto del motor de análisis.

**Razón:** El proyecto académico exige demostrar capacidad de diseño extensible y
permite cambiar de proveedor según costos o disponibilidad.

### 2. Patrón Repository para el acceso a datos

Las consultas viven en `app/repositories/`:

| Repositorio | Responsabilidad |
|---|---|
| `RepositorioUsuarios` | Búsqueda por correo o id, listado con búsqueda sin acentos, perfil, contraseña, estado, invalidación de sesiones, conteo de administradores activos, eliminación |
| `RepositorioAnalisis` | Creación, consulta por usuario, historial con filtros, estadísticas, metadatos del reporte, eliminación |
| `RepositorioCorpusNormativo` | Búsqueda por similitud sobre fragmentos activos, resumen por documento, activación y desactivación, deduplicación por hash |

`json_sql.py` define expresiones portables entre PostgreSQL y SQLite (las pruebas usan
SQLite): lectura de valores dentro de `resultado` (JSONB) y `sin_acentos`, que usa la
extensión `unaccent` en PostgreSQL y una función equivalente en SQLite. Las búsquedas
por texto tratan `%` y `_` como caracteres literales.

**Razón:** Los servicios quedan libres de SQL y se prueban igual en ambos motores.

### 3. PostgreSQL + pgvector como única base de datos

En lugar de una base vectorial separada (Pinecone, Weaviate, Qdrant), se usa la
extensión `pgvector` sobre PostgreSQL. Tanto los datos relacionales (`users`,
`analysis_temp`) como los vectoriales (`corpus_chunks`) conviven en el mismo motor.

La búsqueda por similitud es **exacta** (sin índice vectorial). La migración 0008
eliminó el índice `ivfflat`: se creaba con la tabla vacía, sus listas no
representaban el corpus y devolvía fragmentos menos relevantes que la búsqueda
exacta. Con el tamaño actual del corpus (cientos de fragmentos) la búsqueda exacta
tarda milisegundos. Si el corpus llegara a decenas de miles de fragmentos, conviene
crear un índice nuevo **después** de cargar los datos.

**Razón:** Menor complejidad de infraestructura. Menos servicios = menos puntos de falla.

### 4. Embeddings locales (Sentence Transformers)

El modelo `paraphrase-multilingual-mpnet-base-v2` (~450 MB, 768 dimensiones, vectores
normalizados) se ejecuta dentro del contenedor del backend como singleton que se carga
la primera vez que se usa. La inferencia corre en un hilo aparte para no bloquear el
bucle de eventos mientras otras solicitudes (por ejemplo, la consulta de progreso)
siguen respondiendo.

**Razón:** Costo cero por consulta de embeddings. La política analizada no sale del
servidor para generar embeddings.

### 5. RAG (Retrieval-Augmented Generation)

El motor no pasa el texto completo al modelo de una vez. Para cada sección:
1. Genera el embedding de la sección (768D).
2. Busca los 5 fragmentos **activos** más cercanos en `corpus_chunks` (coseno).
3. Agrega los 2 fragmentos guatemaltecos más cercanos que no estén ya entre esos 5
   (RN-07): sin ellos el modelo casi nunca puede citar normativa nacional.
4. Construye el prompt con la sección y los fragmentos numerados (cada uno con
   documento, jurisdicción, referencia y hasta 600 caracteres de contenido).

**Razón:** Garantiza que el análisis esté fundamentado en fuentes verificables.

### 6. Citas verificables construidas por el servidor (RN-06)

El modelo **no redacta las citas**: por cada hallazgo solo indica los números de los
fragmentos que lo respaldan. El servidor arma cada cita con el texto real del corpus:

- documento: nombre del documento fuente, sin extensión;
- referencia: artículos detectados en el propio fragmento ("Artículo 4",
  "Artículos 3 y 4"), o vacía si no menciona ninguno;
- extracto: texto real del fragmento, hasta 600 caracteres;
- jurisdicción: la del fragmento.

Los números que no corresponden a un fragmento entregado se descartan. Un hallazgo sin
fragmentos válidos queda marcado `sin_respaldo: true`: se muestra señalado en la web y
en el PDF, **no cuenta** para el nivel global ni para la puntuación de riesgo, y sí se
considera para las recomendaciones.

**Razón:** Honestidad académica: ninguna cita puede ser inventada por el modelo.

### 7. System prompt OPP-115 y tipo de tratamiento

El system prompt implementa la taxonomía OPP-115 para clasificar secciones
(First Party Collection, Data Retention, User Choice, etc.), los criterios de riesgo
alto, medio y bajo del diseño del proyecto y la distinción jurisdiccional (Guatemala
no cuenta con una ley integral de protección de datos; las referencias internacionales
se presentan como buena práctica).

Cada hallazgo lleva un **tipo de tratamiento** de una lista cerrada de 8 valores
(recopilación, uso y finalidad, transferencia a terceros, conservación, seguridad,
derechos del usuario, cambios en la política y "Otro"). Se toleran solo diferencias de
mayúsculas o espacios; cualquier otro valor invalida la respuesta. Los análisis
anteriores a esta clasificación no tienen etiqueta.

**Razón:** La taxonomía OPP-115 es el estándar académico más citado para análisis
automatizado de políticas de privacidad.

### 8. Validación JSON con reintento

Si el modelo devuelve una respuesta inválida (JSON malformado, tipo de tratamiento
fuera de la lista o `fragmentos` que no es una lista), el servicio:
1. Intenta extraer el bloque JSON (incluso si viene envuelto en markdown).
2. Si falla, repite la instrucción completa (sección, fragmentos y esquema) junto con
   el motivo del rechazo.
3. Si falla de nuevo, usa una sección de respaldo ("No fue posible analizar esta
   sección automáticamente"), sin afectar a las demás secciones. La sección de
   respaldo lleva `analizada: false`: se muestra, pero **no cuenta** para el nivel
   global ni para la puntuación de riesgo.

**Razón:** Robustez ante comportamiento no determinista del modelo.

### 9. Sesiones con JWT revocables

- El token lleva `sub`, `role` (solo informativo para el cliente), `iat` con fracción
  de segundo, `exp` (24 horas por defecto) y un identificador único `jti`.
- **Cerrar sesión** guarda el `jti` en Redis (`revoked_jti:<jti>`) con un TTL igual al
  tiempo que le queda al token, así la lista se limpia sola. Redis se comparte entre
  instancias, lo que mantiene al servidor sin estado.
- **Cambiar la contraseña** o **desactivar la cuenta** fija `users.sessions_valid_from`:
  se rechaza todo token cuyo `iat` sea anterior. El cambio de contraseña devuelve un
  token nuevo para que la sesión actual continúe.
- **Eliminar la cuenta** revoca el token actual; los demás dejan de servir porque la
  cuenta ya no existe (401).
- En cada solicitud autenticada, `get_current_user` comprueba la revocación, que el
  usuario exista y esté activo, y `sessions_valid_from`. La autorización usa el **rol
  vigente en la base de datos**, no el del token, para que un cambio de rol tenga
  efecto inmediato.

No hay tokens de refresco: al expirar el token, la persona vuelve a iniciar sesión.

### 10. Roles y administración

- Roles: `usuario` (por defecto; el registro público nunca asigna otro) y
  `administrador`, con restricción `CHECK` en la base.
- El rol administrador solo se asigna con `scripts/promover_admin.py`; ninguna ruta de
  la API eleva roles. La persona promovida debe volver a iniciar sesión para que su
  token lleve el rol (el servidor la reconoce como administradora de inmediato).
- Las rutas `/api/admin/*` dependen de `require_admin`:
  - usuarios: listado paginado con búsqueda por nombre o correo (sin acentos),
    activación y desactivación; un administrador no puede desactivarse a sí mismo;
  - corpus: listado por documento (jurisdicción, fragmentos, fecha, estado),
    activación o desactivación del documento completo y carga de documentos nuevos
    (PDF o TXT de hasta 5 MB, como máximo 5 cargas por minuto; el nombre del archivo
    es el identificador y uno repetido responde 409). La carga usa el mismo proceso
    que el script de carga del corpus.
- No se puede eliminar la cuenta del único administrador activo.

### 11. Registros sin datos personales

`app/core/registro.py` configura los registros del servidor:
- los mensajes propios usan el id del usuario, nunca correos ni nombres;
- no se registran nombres de archivos cargados (solo la extensión) ni URL completas
  (solo el nombre del sitio);
- un filtro reemplaza la IP en el aviso que SlowAPI escribe al rechazar una solicitud
  por exceso;
- en producción, uvicorn arranca con `--no-access-log` (ver `backend/Dockerfile`),
  porque el registro de acceso escribiría la IP de cada solicitud. La plataforma de
  despliegue recibe la IP en su propia capa (sección 5 del aviso de privacidad);
- SQLAlchemy solo registra las consultas SQL con sus parámetros (que pueden incluir
  correos) si `SQL_ECHO=true`; está apagado por defecto y no depende de
  `ENVIRONMENT`.

### 12. Protección de la entrada

- Límites de solicitudes por IP con SlowAPI (en memoria): registro 10/min, inicio de
  sesión 5/min, cambio de contraseña 5/min, eliminación de cuenta 5/min, ingesta de
  texto 20/min, de URL 10/min, de archivo 10/min, inicio de análisis 5/min, PDF
  10/min y carga de documentos al corpus 5/min. Al superarlos, la API responde 429
  con `{"detail": "Demasiadas solicitudes. Espera un minuto antes de volver a
  intentarlo."}` (`app/core/manejadores.py`) y el cliente muestra un mensaje claro.
- `LimiteCargaArchivoMiddleware` (`app/core/limite_carga.py`) rechaza con 413 un `POST`
  a `/api/ingesta/archivo` o a `/api/admin/corpus` (`RUTAS_CARGA_ARCHIVO`) cuyo
  `Content-Length` supere 6 MB (el máximo de 5 MB más margen para el formulario),
  antes de leer el cuerpo. El archivo se procesa en memoria y no se guarda.
- Ingesta por URL (`validar_url_publica` y `_descargar` en `ingesta_service.py`): para
  que el servidor no pueda usarse para consultar servicios internos, solo se descargan
  direcciones `http` o `https`, con puerto estándar (80, 443 o sin puerto), sin
  credenciales en la URL y cuyo nombre resuelva solo a IP públicas. Las redirecciones
  se siguen a mano (máximo 5) y cada destino se valida igual.
- El correo se guarda y se busca en minúsculas (`auth_service.normalizar_email`), así
  que el registro y el inicio de sesión no distinguen mayúsculas.
- Regla única de longitud tras la limpieza (RN-01): mínimo 200 caracteres y 40
  palabras, máximo 200,000 caracteres; el texto crudo se limita a 400,000. La misma
  regla se aplica al iniciar el análisis, para que no pueda saltarse llamando a la API.
- Los errores de validación (422) conservan el formato de FastAPI, pero sin el prefijo
  "Value error, " que Pydantic antepone a los mensajes propios.

---

## Flujo completo de una solicitud de análisis

```
Usuario
  │ POST /api/ingesta/texto | /url | /archivo
  ▼
ingesta_service
  │ extraer (URL: validar_url_publica + requests sin redirecciones automáticas
  │          + BeautifulSoup; PDF: pdfplumber → pypdf;
  │          TXT: UTF-8 o Windows-1252)
  │ limpiar_texto() → validar_longitud_politica() (RN-01)
  │ → texto limpio
  ▼
Frontend: vista previa obligatoria del texto
  │ POST /api/analisis/iniciar  {texto}
  ▼
crear_analisis()
  │ AnalysisTemp(estado="procesando"), solo los primeros 2,000 caracteres
  │ se guardan en texto_original (el análisis usa el texto completo) → commit
  │ lanzar_analisis_en_fondo()  →  HTTP 202 {id_analisis, estado}
  ▼
ejecutar_analisis_background()  (sesión de BD propia)
  │ _crear_adaptador_llm()  → OpenAIAdapter (LLM_PROVIDER=openai)
  │
  │ segmentar_politica(texto)       sin tope de secciones
  │   ├── detectar encabezados (numerados, romanos, markdown, MAYÚSCULAS)
  │   ├── secciones de más de 700 palabras → bloques de 500
  │   ├── texto sin encabezados → bloques de 500
  │   └── se descartan secciones de menos de 30 palabras
  │ secciones_total = n → commit
  │
  │ Hasta 4 secciones en paralelo (_CONCURRENCIA_LLM); la búsqueda en el
  │ corpus y el guardado del progreso se serializan con un candado:
  │   │ recuperar_contexto(seccion, k=5, k_guatemala=2)
  │   │   SELECT ... WHERE active ORDER BY embedding <=> :vec LIMIT k
  │   │   (búsqueda exacta, sin índice)
  │   │ llm.generar_analisis(SYSTEM_PROMPT, sección + fragmentos numerados)
  │   │ _parsear_seccion()  → citas armadas desde los números de fragmento
  │   │   (reintento con el motivo si la respuesta es inválida)
  │   │ _respaldar_hallazgos()  segunda pasada, solo si hay hallazgos
  │   │   sin respaldo: busca 3 fragmentos con la descripción de cada uno
  │   │   y una llamada breve elige los que lo respaldan; si falla, la
  │   │   sección queda igual
  │   │ seccion_actual += 1 → commit   (el progreso cuenta secciones listas)
  │
  │ _calcular_resumen()  solo hallazgos con respaldo de secciones analizadas
  │   (las secciones de respaldo, analizada=false, no cuentan)
  │   pesos = [bajo=1, medio=2, alto=3]
  │   puntuación = (promedio - 1) / 2 * 100
  │
  │ _generar_recomendaciones_practicas()  una llamada al final
  │   hasta 15 riesgos altos y medios (altos primero y, dentro de cada
  │   nivel, los respaldados primero) → hasta 5 acciones en imperativo,
  │   ≤ 400 caracteres, sin repetir
  │   sin riesgos altos/medios o si falla → recomendaciones básicas
  │
  │ resultado = AnalisisResponse (JSON), estado = "completado" → commit
  │ ante un error no recuperable: estado = "error"
  ▼
Frontend: sondea GET /api/analisis/{id}/estado (seccion_actual / secciones_total)
  │ al completarse: GET /api/analisis/{id}
  │   (409 si todavía se procesa o si terminó con error)
  └─→ Resultados: resumen, secciones con hallazgos, citas, filtro por nivel
      y jurisdicción (en el cliente), recomendaciones y descarga del PDF
```

La tarea de fondo vive en el proceso del backend: si el servidor se reinicia durante un
análisis, al arrancar (`lifespan` en `app/main.py`) `marcar_analisis_interrumpidos()`
pasa a `error` todos los análisis que quedaron en `procesando`.

El PDF (`GET /api/analisis/{id}/pdf`) se genera con ReportLab bajo demanda; cada
generación registra su duración en `resultado.metadatos_reporte` (últimas 10
mediciones), que resume `scripts/tiempos_reporte.py`.

---

## Modelo de datos

### `users`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | integer, PK | |
| `nombre` | varchar(100) | editable desde el perfil |
| `email` | varchar(255), único | no editable; se guarda en minúsculas |
| `hashed_password` | varchar(255) | bcrypt |
| `is_active` | boolean | la desactivación invalida las sesiones |
| `role` | varchar(20) | `usuario` o `administrador` (`ck_users_role`), por defecto `usuario` |
| `privacy_accepted_at` | timestamptz, obligatoria | aceptación del aviso de privacidad al registrarse |
| `age_declaration_at` | timestamptz, nula | declaración de mayoría de edad o consentimiento; nula solo en cuentas anteriores a la migración 0009 |
| `sessions_valid_from` | timestamptz, nula | se rechazan los tokens emitidos antes |
| `created_at` | timestamptz | |

### `analysis_temp`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | integer, PK | |
| `user_id` | integer, FK → `users.id` | los análisis se eliminan junto con la cuenta |
| `texto_original` | text | primeros 2,000 caracteres de la política |
| `resultado` | JSONB | `AnalisisResponse` completo y, si aplica, `metadatos_reporte` |
| `estado` | varchar(20) | `procesando`, `completado` o `error` |
| `seccion_actual` | integer | secciones ya analizadas |
| `secciones_total` | integer, nula | total tras segmentar |
| `created_at` | timestamptz | |

La eliminación de un análisis es definitiva; uno ajeno o inexistente responde 404 y
uno en curso, 409. Al consultar el detalle o el PDF, uno ajeno o inexistente responde
404, y uno en curso o que terminó con error, 409.

### `corpus_chunks`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | serial, PK | |
| `documento_fuente` | varchar(255) | nombre del archivo; identifica al documento (índice) |
| `jurisdiccion` | varchar(50) | `guatemala`, `internacional` o `estandar_tecnico` (índice) |
| `referencia` | varchar(255) | derivada del nombre del archivo |
| `categoria_tematica` | varchar(100) | inferida del nombre del archivo (índice) |
| `texto_original` | text | fragmento de 300–500 palabras con solapamiento de 50 |
| `embedding` | vector(768) | sin índice vectorial (búsqueda exacta) |
| `metadatos` | JSONB | `hash` MD5 del fragmento para evitar duplicados y ruta u origen |
| `active` | boolean | solo los fragmentos activos participan en la recuperación |
| `fecha_carga` | timestamptz | |

### Migraciones

| Migración | Cambio |
|---|---|
| 0001 | Tabla `users` |
| 0002 | Extensión `vector` y tabla `corpus_chunks` (también puede venir de `postgres/init.sql`, que la crea igual que las migraciones: con `active`, `fecha_carga` con zona horaria e índice `idx_corpus_documento_fuente`) |
| 0003 | Tabla `analysis_temp` |
| 0004 | `seccion_actual` y `secciones_total` (progreso) |
| 0005 | `role`, `privacy_accepted_at` y `sessions_valid_from` en `users` |
| 0006 | `corpus_chunks.active` e índice por documento fuente |
| 0007 | Extensión `unaccent` (búsquedas sin acentos) |
| 0008 | Elimina el índice `ivfflat` (búsqueda exacta) |
| 0009 | `users.age_declaration_at` |
| 0010 | Correos de `users` en minúsculas (se detiene si dos cuentas solo difieren en mayúsculas) |

---

## Estructura de módulos del backend

```
app/
├── main.py              # FastAPI app (VERSION_API), lifespan, CORS, SlowAPI, límite de carga, routers
├── config.py            # Pydantic Settings (variables de entorno)
├── database.py          # Async engine, AsyncSessionLocal, get_db()
├── api/
│   ├── deps.py          # usuario actual, revocación, sessions_valid_from, require_admin
│   └── v1/
│       ├── auth.py      # /register /login /logout /me (GET, PATCH, DELETE) /change-password
│       ├── ingesta.py   # /texto /url /archivo
│       ├── analisis.py  # /iniciar /estadisticas /{id}/estado /{id} /{id}/pdf, historial, DELETE /{id}
│       └── admin.py     # /usuarios /usuarios/{id}/estado /corpus /corpus/estado
├── core/
│   ├── security.py      # JWT (python-jose, con jti) + bcrypt (passlib)
│   ├── token_revocation.py  # lista de jti revocados en Redis
│   ├── exceptions.py    # HTTPExceptions personalizadas con status codes
│   ├── limiter.py       # slowapi Limiter (por IP)
│   ├── limite_carga.py  # rechazo temprano por Content-Length
│   ├── manejadores.py   # respuestas 429 y 422 con formato {"detail": ...}
│   └── registro.py      # registros sin datos personales
├── models/
│   ├── user.py          # User
│   ├── corpus.py        # CorpusChunk (vector(768), active)
│   └── analysis.py      # AnalysisTemp (resultado JSONB, progreso)
├── repositories/
│   ├── usuarios.py      # RepositorioUsuarios
│   ├── analisis.py      # RepositorioAnalisis, FiltrosHistorial
│   ├── corpus.py        # RepositorioCorpusNormativo
│   └── json_sql.py      # expresiones portables PostgreSQL/SQLite
├── schemas/             # auth, user, ingesta, analysis, analisis_request, admin, corpus
├── services/
│   ├── auth_service.py      # registro, login, perfil, contraseña, eliminar cuenta, promover
│   ├── ingesta_service.py   # limpieza, URL (solo sitios públicos), archivo PDF/TXT
│   ├── rag_service.py       # recuperar_contexto (pgvector), contar_chunks
│   ├── analisis_service.py  # segmentación, análisis en segundo plano, resumen,
│   │                        # recomendaciones, historial, estadísticas, fábrica del LLM
│   ├── reportes_service.py  # PDF con ReportLab, jurisdicción de las citas
│   ├── admin_service.py     # gestión de usuarios
│   ├── corpus_service.py    # listado, estado y carga de documentos del corpus
│   └── llm/
│       ├── base.py          # LLMAdapter (ABC)
│       └── openai_adapter.py  # OpenAIAdapter (tenacity retries)
└── utils/
    ├── chunking.py          # chunk_texto (solapamiento 50 palabras)
    ├── embeddings.py        # SentenceTransformer singleton, encode/encode_batch
    ├── pdf_extractor.py     # pdfplumber → pypdf fallback
    └── validacion_texto.py  # regla única de longitud (RN-01)
```

La jurisdicción que se muestra en cada cita se deduce del nombre del documento con las
mismas claves en `frontend/src/utils/jurisdiccion.ts` y en
`reportes_service._inferir_jurisdiccion`. Si se agregan al corpus documentos con
nombres nuevos, hay que ampliar las claves en ambos archivos.

---

## Cambios respecto al marco teórico original

| Aspecto | Diseño original | Implementación final | Justificación |
|---|---|---|---|
| Motor de análisis | Palabras clave + regex | RAG + LLM (OpenAI `gpt-4o-mini`) | Precisión y explicabilidad significativamente superiores |
| Base vectorial | Pinecone (separada) | pgvector en PostgreSQL, búsqueda exacta | Menor complejidad, suficiente para el volumen |
| Embeddings | API externa | Sentence Transformers local | Costo cero + privacidad del texto |
| Citas normativas | No especificadas | Armadas por el servidor desde los fragmentos | Ninguna cita inventada por el modelo |
| Validación LLM | No prevista | Reintento con la instrucción completa y el motivo | Robustez ante respuestas malformadas |
| Segmentación | No especificada | Encabezados + bloques de 500 palabras, sin tope | Cobertura completa de la política |
| Sesiones | JWT simple | JWT con `jti` revocable en Redis e invalidación global | Cierre de sesión real y seguridad ante cambios de contraseña |

Estos cambios están documentados en [`CHANGELOG.md`](../CHANGELOG.md) en la sección
"Decisiones técnicas documentadas" y representan mejoras técnicas respecto al diseño
inicial, justificadas para transparencia académica.
