# Manual Técnico — PrivApp
## Sistema de Análisis Automatizado de Políticas de Privacidad

**Proyecto de Graduación — Universidad Mariano Gálvez, Campus Jutiapa**
**Autor:** Jairo Ardani Castillo Girón — Carné 0905-22-12005
**Fecha:** Septiembre 2026 (primera versión: mayo 2026)
**Versión del sistema:** versión completa de Proyecto de Graduación II (API `2.0.0`)

---

## Índice

1. [Descripción General](#1-descripción-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Estructura del Proyecto](#4-estructura-del-proyecto)
5. [Base de Datos y Migraciones](#5-base-de-datos-y-migraciones)
6. [Backend — API REST](#6-backend--api-rest)
7. [Motor de Análisis con IA](#7-motor-de-análisis-con-ia)
8. [Arquitectura RAG y Corpus Normativo](#8-arquitectura-rag-y-corpus-normativo)
9. [Adaptadores LLM](#9-adaptadores-llm)
10. [Frontend — Interfaz de Usuario](#10-frontend--interfaz-de-usuario)
11. [Cuentas, Sesiones y Roles](#11-cuentas-sesiones-y-roles)
12. [Privacidad del Propio Sistema](#12-privacidad-del-propio-sistema)
13. [Seguridad](#13-seguridad)
14. [Configuración, Despliegue y Scripts](#14-configuración-despliegue-y-scripts)
15. [Pruebas Automatizadas](#15-pruebas-automatizadas)
16. [Historial de Sprints](#16-historial-de-sprints)
17. [Variables de Entorno](#17-variables-de-entorno)
18. [Flujos Principales](#18-flujos-principales)

---

## 1. Descripción General

**PrivApp** es un sistema web que analiza automáticamente políticas de privacidad de plataformas digitales y genera reportes comprensibles para jóvenes ciudadanos de Guatemala. El sistema combina Inteligencia Artificial generativa (OpenAI GPT-4o-mini) con recuperación semántica de normativa (RAG sobre PostgreSQL + pgvector) para identificar riesgos de privacidad, clasificarlos por nivel de severidad y tipo de tratamiento de datos, y presentarlos en lenguaje accesible.

### Problema que resuelve

Los jóvenes de San José Acatempa, Jutiapa (y Guatemala en general) aceptan políticas de privacidad sin leerlas ni comprenderlas, exponiéndose a prácticas abusivas de tratamiento de datos como:
- Recopilación de datos biométricos sin finalidad declarada
- Transferencia a terceros no identificados
- Almacenamiento indefinido e irrenunciable
- Ausencia de mecanismos para eliminar datos personales

### Solución implementada

El usuario ingresa una política de privacidad de tres formas (texto pegado, URL o archivo PDF/TXT), revisa una vista previa del texto extraído y, al confirmar, recibe:
- Un nivel de riesgo global (bajo / medio / alto) con una **puntuación de riesgo** de 0 a 100
- Un desglose de **toda** la política por secciones, con hallazgos específicos clasificados por tipo de tratamiento de datos
- Citas normativas **verificables**, construidas por el servidor con el texto real de los fragmentos del corpus (los hallazgos sin respaldo se marcan como tales)
- Recomendaciones prácticas redactadas a partir de los riesgos encontrados
- Un reporte descargable en PDF

Además ofrece historial con filtros, panel estadístico personal, glosario público, aviso de privacidad, gestión del perfil (incluida la eliminación de la cuenta) y un módulo de administración de usuarios y del corpus normativo.

---

## 2. Arquitectura del Sistema

El sistema sigue una arquitectura de **capas desacopladas** desplegada mediante Docker Compose (cuatro servicios: `db`, `redis`, `backend`, `frontend`):

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUARIO (navegador)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (puerto 5173)
┌────────────────────────────▼────────────────────────────────────┐
│                    FRONTEND (React + Vite)                        │
│   SPA con autenticación JWT, vista previa, progreso del análisis, │
│   resultados, historial, panel, glosario, perfil y administración │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (puerto 8000)
┌────────────────────────────▼────────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                      │
│                                                                   │
│  ┌──────────┐ ┌───────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ Auth API │ │ Ingesta   │ │ Análisis API │ │ Admin API      │  │
│  └──────────┘ └───────────┘ └──────┬───────┘ └────────────────┘  │
│                                    │ tarea en segundo plano       │
│  ┌─────────────────────────────────▼──────────────────────────┐  │
│  │               Motor de Análisis                             │  │
│  │ Segmentación → RAG → LLM (paralelo) → Citas → 2ª pasada     │  │
│  │ → Resumen → Recomendaciones prácticas                       │  │
│  └───────┬─────────────────────────────────────┬──────────────┘  │
│          │ SQLAlchemy Async                    │ OpenAI API      │
│  ┌───────▼───────────────┐  ┌──────────┐  ┌────▼──────────────┐  │
│  │ PostgreSQL + pgvector │  │  Redis   │  │ GPT-4o-mini       │  │
│  │ usuarios, análisis,   │  │ jti      │  │ (OpenAI)          │  │
│  │ corpus normativo      │  │ revocados│  │                   │  │
│  └───────────────────────┘  └──────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes principales

| Componente | Responsabilidad |
|---|---|
| **Frontend** | SPA React: autenticación, ingesta (texto/URL/archivo) con vista previa, seguimiento del progreso, resultados, historial, panel estadístico, glosario, aviso de privacidad, perfil y administración |
| **Backend API** | FastAPI: endpoints REST, validación, límites de solicitudes y orquestación de la lógica de negocio |
| **Servicios** | `auth_service`, `ingesta_service`, `analisis_service`, `rag_service`, `corpus_service`, `admin_service`, `reportes_service` |
| **Repositorios** | Acceso a datos separado por entidad: `RepositorioUsuarios`, `RepositorioAnalisis`, `RepositorioCorpusNormativo` |
| **Motor de Análisis** | Segmenta la política completa, recupera normativa, llama al modelo con concurrencia limitada y construye las citas |
| **RAG Service** | Recupera fragmentos normativos activos por similitud coseno (búsqueda exacta) |
| **LLM Adapter** | Abstracción sobre el proveedor del modelo (hoy solo OpenAI) con reintentos exponenciales |
| **PostgreSQL + pgvector** | Usuarios, análisis y corpus normativo con embeddings de 768 dimensiones |
| **Redis** | Lista de revocación de tokens (`jti`) al cerrar sesión o eliminar la cuenta |

---

## 3. Stack Tecnológico

### Backend

| Tecnología | Versión | Rol |
|---|---|---|
| Python | 3.11 | Lenguaje del backend |
| FastAPI | 0.115.5 | Framework API REST asíncrono |
| Uvicorn | 0.32.1 | Servidor ASGI |
| SQLAlchemy | 2.0.36 | ORM asíncrono (AsyncSession) |
| Alembic | 1.14.0 | Migraciones de base de datos |
| asyncpg | 0.30.0 | Driver PostgreSQL async |
| pgvector | 0.3.6 | Tipo vectorial para SQLAlchemy |
| Pydantic v2 / pydantic-settings | 2.10.3 / 2.6.1 | Validación de datos y configuración |
| OpenAI SDK | 1.82.0 | Cliente de GPT-4o-mini |
| Sentence Transformers (torch CPU) | 3.3.1 | Generación de embeddings de 768 dimensiones |
| python-jose | 3.3.0 | JWT (HS256) |
| passlib + bcrypt | 1.7.4 / 3.2.2 | Hashing de contraseñas |
| redis (cliente async) | 5.2.1 | Lista de revocación de tokens |
| tenacity | 9.0.0 | Reintentos con backoff exponencial |
| slowapi | 0.1.9 | Límite de solicitudes por endpoint |
| pdfplumber / pypdf | 0.11.4 / 5.1.0 | Extracción de texto de PDF (pypdf como respaldo) |
| BeautifulSoup4 + requests | 4.12.3 / 2.32.3 | Extracción de texto desde URL |
| python-multipart | 0.0.20 | Carga de archivos (multipart) |
| ReportLab | 4.2.5 | Generación del reporte PDF |
| pytest + pytest-asyncio + aiosqlite | 8.3.4 / 0.24.0 / 0.20.0 | Suite de pruebas |

### Frontend

| Tecnología | Versión (package.json) | Rol |
|---|---|---|
| React | ^18.3.1 | Librería UI |
| TypeScript | ^5.7.2 | Tipado estático |
| Vite | ^6.0.5 | Bundler y servidor de desarrollo |
| React Router | ^6.28.1 | Enrutamiento |
| Tailwind CSS | ^3.4.17 | Estilos utility-first |
| Axios | ^1.7.9 | Cliente HTTP |
| recharts | ^2.13.3 | Gráfico del panel estadístico (carga diferida) |
| lucide-react | ^0.468.0 | Íconos |
| Headless UI (`@headlessui/react`) | ^2.2.10 | Componentes accesibles sin estilos (diálogo de confirmación: foco retenido, Escape) |
| Figtree (fuente, SIL OFL) | — | Tipografía, servida desde `public/fonts/` |
| Vitest + Testing Library + jsdom | ^2.1.8 / ^16.1.0 / ^25.0.1 | Pruebas del cliente |

### Infraestructura

| Tecnología | Rol |
|---|---|
| Docker + Docker Compose | Contenedorización de los 4 servicios |
| `pgvector/pgvector:pg16` | PostgreSQL 16 con extensión vectorial |
| `redis:7-alpine` | Lista de revocación de tokens |
| `node:20-slim` | Imagen del frontend (servidor de desarrollo de Vite) |
| `python:3.11-slim` | Imagen del backend |

---

## 4. Estructura del Proyecto

```
PrivApp/
├── .env                          ← Variables de entorno (NO en git)
├── .env.example                  ← Plantilla de variables (sin valores reales)
├── docker-compose.yml            ← db, redis, backend, frontend
├── CHANGELOG.md
│
├── backend/
│   ├── Dockerfile                ← Arranque de producción (sin --reload)
│   ├── requirements.txt
│   ├── pyproject.toml            ← Configuración de pytest, black, isort
│   ├── alembic.ini
│   │
│   ├── app/
│   │   ├── main.py               ← FastAPI (VERSION_API), lifespan, middlewares, routers, /health
│   │   ├── config.py             ← Settings (pydantic-settings)
│   │   ├── database.py           ← Engine async + get_db
│   │   │
│   │   ├── api/
│   │   │   ├── deps.py           ← get_current_user, require_admin
│   │   │   └── v1/
│   │   │       ├── auth.py       ← /api/auth/*
│   │   │       ├── ingesta.py    ← /api/ingesta/*
│   │   │       ├── analisis.py   ← /api/analisis/*
│   │   │       └── admin.py      ← /api/admin/* (solo administrador)
│   │   │
│   │   ├── core/
│   │   │   ├── security.py       ← JWT (iat, jti, role), bcrypt
│   │   │   ├── token_revocation.py ← Revocación de jti en Redis
│   │   │   ├── exceptions.py     ← HTTPException personalizadas
│   │   │   ├── limiter.py        ← Instancia global de SlowAPI (clave: IP)
│   │   │   ├── limite_carga.py   ← Rechazo temprano de archivos por Content-Length
│   │   │   ├── manejadores.py    ← Respuestas 429 y 422 con formato {"detail": ...}
│   │   │   └── registro.py       ← Registros sin datos personales
│   │   │
│   │   ├── models/               ← user.py, analysis.py, corpus.py
│   │   ├── repositories/         ← usuarios.py, analisis.py, corpus.py, json_sql.py
│   │   ├── schemas/              ← auth, analysis, analisis_request, ingesta, admin, corpus, user
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py   ← registro, login, perfil, contraseña, eliminar cuenta
│   │   │   ├── admin_service.py  ← listado y estado de usuarios
│   │   │   ├── corpus_service.py ← listado, estado y carga de documentos del corpus
│   │   │   ├── ingesta_service.py← texto, URL (solo sitios públicos) y archivo
│   │   │   ├── analisis_service.py ← MOTOR PRINCIPAL (ver sección 7)
│   │   │   ├── rag_service.py    ← recuperar_contexto
│   │   │   ├── reportes_service.py ← PDF y tiempos de generación
│   │   │   └── llm/
│   │   │       ├── base.py       ← LLMAdapter (ABC)
│   │   │       └── openai_adapter.py ← GPT-4o-mini
│   │   │
│   │   └── utils/
│   │       ├── embeddings.py     ← paraphrase-multilingual-mpnet-base-v2
│   │       ├── chunking.py       ← Segmentación del corpus
│   │       ├── pdf_extractor.py  ← PDF desde disco o desde memoria
│   │       └── validacion_texto.py ← Regla única de longitud (RN-01)
│   │
│   ├── migrations/versions/      ← 0001 … 0011 (ver sección 5)
│   │
│   ├── scripts/
│   │   ├── cargar_corpus.py      ← Carga del corpus normativo
│   │   ├── promover_admin.py     ← Asigna el rol administrador
│   │   └── tiempos_reporte.py    ← Estadísticas del tiempo del reporte PDF
│   │
│   └── tests/                    ← pytest (SQLite) + tests/integracion (PostgreSQL)
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json / vite.config.ts / tailwind.config.js
│   └── src/
│       ├── App.tsx               ← Rutas
│       ├── api/                  ← client, auth, ingesta, analisis, admin
│       ├── components/
│       │   ├── common/           ← Navbar, Footer, ProtectedRoute, AdminRoute, DialogoConfirmacion…
│       │   ├── auth/             ← LoginForm, RegisterForm
│       │   ├── ingesta/          ← IngestaForm, VistaPreviaTexto
│       │   ├── analisis/         ← IndicadorSemaforo, TarjetaSeccion, CitaNormativa,
│       │   │                       FiltroHallazgos, ListaRecomendaciones, VistaProgreso
│       │   ├── historial/        ← FormFiltrosHistorial
│       │   ├── dashboard/        ← PanelEstadistico, GraficoDistribucion
│       │   ├── glosario/         ← AyudaGlosario
│       │   ├── perfil/           ← FormCambioPassword, FormEliminarCuenta
│       │   └── admin/            ← FormCargaDocumento
│       ├── pages/                ← Login, Register, Dashboard, Ingesta, Resultados, Historial,
│       │                           Perfil, Glosario, AvisoPrivacidad, Admin, AdminUsuarios, AdminCorpus
│       ├── data/                 ← avisoPrivacidad.ts, glosario.ts, consejosPrivacidad.ts
│       ├── context/              ← AuthContext (JWT en localStorage)
│       ├── hooks/                ← useAuth, useAnalisis, useHistorial, useProgresoAnalisis, useUsuariosAdmin
│       ├── utils/                ← validators, errores, jurisdiccion, filtrosHallazgos
│       └── test/                 ← setup.ts, fixtures.ts
│
├── postgres/
│   └── init.sql                  ← Extensiones vector y uuid-ossp + tabla corpus_chunks (igual que las migraciones)
│
├── docs/                         ← api.md, arquitectura.md, instalacion.md, guia_evaluador.md
│
└── corpus_normativo/             ← Documentos fuente del corpus RAG
    ├── guatemala/
    ├── internacional/
    ├── estandares_tecnicos/
    └── originales/               ← Documentos fuente que no se cargan
```

---

## 5. Base de Datos y Migraciones

### Motor

**PostgreSQL 16** con extensión **pgvector** (`pgvector/pgvector:pg16`). Se usa `AsyncSession` de SQLAlchemy para todas las operaciones. Extensiones utilizadas: `vector` (init.sql y migración 0002), `uuid-ossp` (init.sql) y `unaccent` (migración 0007).

### Tablas

#### `users` (migraciones 0001, 0005, 0009 y 0010)
```sql
CREATE TABLE users (
    id                   SERIAL PRIMARY KEY,
    nombre               VARCHAR(100) NOT NULL,
    email                VARCHAR(255) UNIQUE NOT NULL,              -- en minúsculas (0010)
    hashed_password      VARCHAR(255) NOT NULL,
    is_active            BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    role                 VARCHAR(20)  NOT NULL DEFAULT 'usuario',   -- 0005
    privacy_accepted_at  TIMESTAMPTZ  NOT NULL,                     -- 0005
    sessions_valid_from  TIMESTAMPTZ,                               -- 0005
    age_declaration_at   TIMESTAMPTZ,                               -- 0009
    CONSTRAINT ck_users_role CHECK (role IN ('usuario', 'administrador'))
);
```

- `email`: se guarda y se busca en minúsculas (`auth_service.normalizar_email`), así que "Ana@Ejemplo.com" y "ana@ejemplo.com" son la misma cuenta. La migración 0010 normalizó los correos existentes.
- `role`: `usuario` o `administrador`. El registro público siempre asigna `usuario`.
- `privacy_accepted_at`: fecha de aceptación del aviso de privacidad (obligatoria).
- `sessions_valid_from`: solo se aceptan tokens emitidos después de esta fecha (ver sección 11).
- `age_declaration_at`: fecha de la declaración de mayoría de edad o de consentimiento de la madre, el padre o la persona encargada. Es nula solo en cuentas creadas antes de la migración 0009.

#### `corpus_chunks` (postgres/init.sql, migraciones 0002, 0006 y 0008)
```sql
CREATE TABLE corpus_chunks (
    id                  SERIAL PRIMARY KEY,
    documento_fuente    VARCHAR(255) NOT NULL,  -- nombre del archivo (identificador del documento)
    jurisdiccion        VARCHAR(50)  NOT NULL,  -- 'guatemala' | 'internacional' | 'estandar_tecnico'
    referencia          VARCHAR(255),
    categoria_tematica  VARCHAR(100),
    texto_original      TEXT         NOT NULL,
    embedding           vector(768)  NOT NULL,  -- paraphrase-multilingual-mpnet-base-v2
    metadatos           JSONB,                  -- incluye "hash" (deduplicación)
    fecha_carga         TIMESTAMPTZ  DEFAULT NOW(),
    active              BOOLEAN      NOT NULL DEFAULT TRUE   -- 0006
);
-- Índices: jurisdiccion, categoria_tematica y documento_fuente (idx_corpus_documento_fuente, 0006).
-- postgres/init.sql crea la tabla con las mismas columnas e índices que las migraciones.
-- Sin índice vectorial aproximado: la migración 0008 elimina el ivfflat (ver sección 8).
```

#### `analysis_temp` (migraciones 0003, 0004 y 0011)
```sql
CREATE TABLE analysis_temp (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    texto_original  TEXT    NOT NULL,   -- solo los primeros 2,000 caracteres de la política
    resultado       JSONB,              -- AnalisisResponse serializado (+ metadatos_analisis, metadatos_reporte)
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente', -- procesando | completado | error
    seccion_actual  INTEGER NOT NULL DEFAULT 0,  -- 0004: secciones ya analizadas
    secciones_total INTEGER,                     -- 0004
    text_hash       VARCHAR(64),                 -- 0011: SHA-256 del texto analizado (reutilización)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_analysis_temp_text_hash ON analysis_temp(text_hash);  -- 0011
```

> **Nota técnica:** solo se guarda un extracto de 2,000 caracteres del texto de la política (se usa en la búsqueda del historial); el análisis se realiza siempre sobre el texto completo, que no se persiste. El campo `resultado` usa `JSONB` en PostgreSQL y un `TypeDecorator` (`JSONBCompat`) que lo mapea a `TEXT` en SQLite (pruebas). Las consultas dentro del JSON y la búsqueda sin acentos se escriben con expresiones portables (`repositories/json_sql.py`: `json_texto`, `sin_acentos`).

### Migraciones Alembic

| Revisión | Contenido |
|---|---|
| 0001 | Tabla `users` |
| 0002 | Extensión `vector`, tabla `corpus_chunks` (si no existe) e índices (incluido el ivfflat, eliminado luego por 0008) |
| 0003 | Tabla `analysis_temp` |
| 0004 | Progreso del análisis: `seccion_actual`, `secciones_total` |
| 0005 | `users.role` (con restricción de valores), `privacy_accepted_at`, `sessions_valid_from` |
| 0006 | `corpus_chunks.active` e índice por `documento_fuente` |
| 0007 | Extensión `unaccent` (búsquedas sin distinguir acentos). **Requiere un usuario de base de datos con permiso para `CREATE EXTENSION`** |
| 0008 | Elimina el índice ivfflat de `corpus_chunks.embedding` (búsqueda exacta) |
| 0009 | `users.age_declaration_at` |
| 0010 | Pasa a minúsculas los correos de `users` (la migración inversa no restaura las mayúsculas) |
| 0011 | `analysis_temp.text_hash` (nullable) e índice: reutilización del resultado de un texto idéntico (sección 7) |

> **Advertencia sobre 0005:** `privacy_accepted_at` es obligatoria y no tiene valor por defecto; si la tabla `users` ya tuviera filas, la migración falla en lugar de inventar una aceptación que no ocurrió.

> **Advertencia sobre 0010:** si dos cuentas solo se distinguen por mayúsculas en el correo, la migración se detiene y las lista; hay que resolverlas a mano (no se fusionan cuentas automáticamente) y volver a ejecutarla.

```bash
# Aplicar migraciones pendientes (no se ejecutan solas al arrancar)
docker compose exec backend alembic upgrade head

# Ver revisión actual
docker compose exec backend alembic current

# Crear nueva migración
docker compose exec backend alembic revision --autogenerate -m "descripcion"
```

---

## 6. Backend — API REST

Documentación interactiva generada por FastAPI en `/docs` (Swagger) y `/redoc`. Todas las rutas, salvo registro, inicio de sesión y `/health`, requieren `Authorization: Bearer <token>`.

### Límites de solicitudes

SlowAPI, por dirección IP, con contador en memoria del proceso. Al superarlos la API responde **429** con `{"detail": "Demasiadas solicitudes. Espera un minuto antes de volver a intentarlo."}` (`app/core/manejadores.py`) y el cliente muestra: *"Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo."* (`frontend/src/utils/errores.ts`).

| Ruta | Límite |
|---|---|
| `POST /api/auth/register` | 10/min |
| `POST /api/auth/login` | 5/min |
| `POST /api/auth/change-password` | 5/min |
| `DELETE /api/auth/me` | 5/min |
| `POST /api/ingesta/texto` | 20/min |
| `POST /api/ingesta/url` | 10/min |
| `POST /api/ingesta/archivo` | 10/min |
| `POST /api/analisis/iniciar` | 5/min |
| `GET /api/analisis/{id}/pdf` | 10/min |
| `POST /api/admin/corpus` | 5/min |

### Autenticación y perfil — `/api/auth`

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/register` | Registro (`nombre`, `email`, `password`, `acepta_aviso`, `declara_edad`) → JWT (201) |
| `POST` | `/login` | Autenticación → JWT; las cuentas inactivas se rechazan con 401 |
| `POST` | `/logout` | Revoca el `jti` del token actual en Redis hasta su expiración |
| `GET` | `/me` | Perfil: `id`, `nombre`, `email`, `role` |
| `PATCH` | `/me` | Edita el nombre (el correo no es editable) |
| `DELETE` | `/me` | Elimina la cuenta y todos sus análisis (cuerpo `{password}`) → 204 |
| `POST` | `/change-password` | `password_actual`, `password_nueva`, `confirmar_password` → token nuevo |

**Validaciones:**
- Contraseña: 8–100 caracteres, al menos una mayúscula y un número (registro y cambio de contraseña).
- Email: formato válido (`email-validator`); se guarda y se busca en minúsculas, así que el registro y el inicio de sesión no distinguen mayúsculas. Nombre: 2–100 caracteres.
- `acepta_aviso` y `declara_edad` deben ser `true` (422 en caso contrario).
- Cambio de contraseña: 400 si la actual es incorrecta o si la nueva es igual a la actual; 422 si la confirmación no coincide.
- Eliminación de cuenta: 400 si la contraseña es incorrecta o si la persona es el único administrador activo; 409 si tiene un análisis en curso.

### Ingesta — `/api/ingesta`

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/texto` | Texto pegado (`{texto}`) |
| `POST` | `/url` | Descarga la página y extrae el texto (`{url}`) |
| `POST` | `/archivo` | Formulario multipart con el campo `archivo` (PDF o TXT) |

Las tres rutas devuelven `IngestaResponse` (`texto_procesado`, `caracteres`, `palabras`, `fuente`, `deteccion`) y **no inician el análisis**: el cliente muestra una vista previa obligatoria y solo al confirmarla llama a `/api/analisis/iniciar`.

**¿Es una política de privacidad? (RN-18, `services/deteccion_politica.py`)** — tras la regla de longitud, cada vía de ingesta y de nuevo `/api/analisis/iniciar` evalúan si el texto es una política de privacidad o un documento que explica el tratamiento de datos personales. Son tres señales deterministas, sin llamar al modelo de lenguaje:

| Señal | Qué mide |
|---|---|
| Temas | Cuántos de 10 temas típicos aparecen (datos personales, privacidad, finalidad, terceros, conservación, derechos, cookies, seguridad, contacto del responsable, cambios), en español o inglés, sin distinguir tildes |
| Cobertura | Fracción de fragmentos de 80 palabras (hasta 40, repartidos por el texto) cuya semejanza con 12 cláusulas típicas, según el modelo de embeddings del corpus, es ≥ 0.45 |
| Voz del responsable | Expresiones con las que el responsable describe sus prácticas: "recopilamos", "compartimos", "nuestros servicios", "we collect"... o en tercera persona ("la empresa utilizará") |

Decisión: **`politica`** si hay ≥ 5 temas, cobertura ≥ 0.30 y ≥ 3 expresiones de voz; **`no_politica`** si hay ≤ 2 temas y cobertura < 0.25 (422 "El texto no parece una política de privacidad..."); **`dudosa`** en los demás casos. Un texto dudoso pasa a la vista previa con un aviso, y `/api/analisis/iniciar` exige `confirma_politica: true` (si no, 422). Sin voz del responsable un texto nunca pasa solo, pero tampoco se rechaza por eso: hay políticas redactadas de forma impersonal. El resultado de los últimos 16 textos se recuerda para no recalcular los embeddings entre la ingesta y el inicio.

Umbrales calibrados con `scripts/evaluar_deteccion.py` sobre 22 textos (03/10/2026): 7 de 7 políticas reales y 5 de 5 documentos parecidos (términos de servicio, política de cookies, una política impersonal, un artículo sobre protección de datos) pasan o quedan dudosos; de 10 textos que no son políticas (artículos de Wikipedia, una receta, una tarea, un cuento), 9 se rechazan y 1 (un artículo enciclopédico sobre privacidad) queda dudoso. **Ninguno pasa sin confirmación.**

**Red de seguridad después del análisis** — si casi ninguna sección cumple un criterio de la rúbrica (menos de 3 hallazgos y menos del 20 % de las secciones analizadas con hallazgos), el análisis termina con `estado = error` y `resultado = {"motivo_error": "no_es_politica"}`: no recibe puntuación, no aparece en el historial ni en las estadísticas, y `GET /{id}/estado` devuelve `motivo: "no_es_politica"` para que el cliente lo explique.

**Regla única de longitud (RN-01, `utils/validacion_texto.py`)** — se aplica siempre sobre el texto ya limpio, en las tres vías y de nuevo en `/api/analisis/iniciar`:
- Mínimo **200 caracteres y 40 palabras**; máximo **300,000 caracteres** (alcanza, por ejemplo, para la declaración de privacidad completa de Microsoft, de unos 252,000 caracteres y 77 secciones, que se analiza en unos minutos). El mensaje de error indica cuánto mide el texto y sugiere copiar solo la parte general o la del servicio que se usa.
- Tope previo del texto crudo recibido: **400,000 caracteres** (solo evita procesar entradas desproporcionadas; la limpieza puede reducir mucho la longitud).

**Limpieza (`ingesta_service.limpiar_texto`):** normalización Unicode NFC, eliminación de caracteres de control, colapso de espacios por línea, máximo un párrafo en blanco consecutivo.

**URL:** tiempo de espera de 10 s; solo acepta respuestas HTML; descarta `script`, `style`, `nav`, `header`, `footer`, `aside` y `form`, y toma el contenido de `main`, `article` o `body`.

Solo se descargan sitios web públicos (`validar_url_publica`), para que el servidor no pueda usarse para consultar servicios internos:
- esquema `http` o `https` (si no: 422 *"La dirección debe comenzar con http:// o https://."*);
- puerto estándar (80, 443 o sin puerto) y sin usuario ni contraseña en la URL;
- el nombre del sitio debe resolver solo a direcciones IP públicas (si no: 422 *"La dirección indicada no es un sitio web público."*; si no resuelve: *"No se pudo conectar a la URL proporcionada."*).

`_descargar` sigue las redirecciones a mano (`allow_redirects=False`), como máximo 5, y valida cada destino con las mismas reglas; más de 5 → 422 *"La URL redirige demasiadas veces."* Queda la posibilidad teórica de que el DNS cambie entre la validación y la descarga.

**Archivo:**
- Solo `.pdf` (`application/pdf`, `application/x-pdf`) o `.txt` (`text/plain`); extensión y tipo deben coincidir; un PDF debe empezar con `%PDF-` (415 en caso contrario).
- Tamaño máximo **5 MB** (413). Rechazo temprano: el middleware `LimiteCargaArchivoMiddleware` responde 413 a partir de la cabecera `Content-Length` (umbral de 6 MB, para dejar margen al encabezado multipart) antes de leer el cuerpo.
- Procesado **solo en memoria**: se sube el umbral de Starlette (`MultiPartParser.max_file_size`) por encima de 5 MB para que un archivo válido no se escriba en un archivo temporal en disco. El archivo no se guarda en ningún lugar.
- TXT en UTF-8 (con o sin BOM) o, si no lo es, Windows-1252.
- PDF sin texto extraíble (por ejemplo, escaneado; no hay OCR) → 422 con un mensaje que sugiere pegar el texto.

### Análisis — `/api/analisis`

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/iniciar` | `{texto, confirma_politica}`: crea el análisis y lo procesa en segundo plano → 202 `{id_analisis, estado: "procesando"}` |
| `GET` | `/{id}/estado` | Progreso: `estado` (`procesando`/`completado`/`error`), `seccion_actual`, `secciones_total` y `motivo` (`no_es_politica` o `null`) |
| `GET` | `/{id}` | Resultado completo (solo si está `completado`; si está en curso o terminó con error, 409) |
| `GET` | `` (raíz) | Historial paginado con filtros |
| `GET` | `/estadisticas` | Totales del usuario para el panel |
| `GET` | `/{id}/pdf` | Descarga el reporte PDF (`privapp-analisis-{id}.pdf`) |
| `DELETE` | `/{id}` | Elimina el análisis de forma definitiva → 204 |

Todas las consultas se limitan a los análisis del usuario autenticado: un análisis ajeno o inexistente responde **404** (sin revelar si existe).

**Detalle y PDF (`GET /api/analisis/{id}` y `/{id}/pdf`):** 404 solo si no existe o es ajeno; 409 *"El análisis todavía se está procesando."* si está en curso; 409 *"El análisis no pudo completarse. Intenta analizar la política de nuevo."* si terminó con error.

**Historial (`GET /api/analisis`):** parámetros `page` (≥1), `page_size` (1–50, por defecto 10), `nivel` (`bajo`/`medio`/`alto`), `desde` y `hasta` (ISO 8601, inclusivos; las fechas sin zona se toman como UTC) y `q` (máx. 100 caracteres). Solo lista análisis completados, del más reciente al más antiguo. `q` busca en el extracto de la política y en el comentario del resumen, sin distinguir mayúsculas ni acentos (`unaccent`), y trata `%` y `_` como caracteres literales. `desde` posterior a `hasta` → 422.

**Estadísticas (`GET /api/analisis/estadisticas`):** `{total, por_nivel: {bajo, medio, alto}, puntaje_promedio}` sobre los análisis completados; todo en cero si el usuario aún no tiene análisis.

**Eliminación (`DELETE /api/analisis/{id}`):** definitiva (no hay papelera); 404 si es ajeno o no existe; 409 si todavía está en proceso.

**Request de análisis:**
```json
{ "texto": "POLÍTICA DE PRIVACIDAD... (texto ya limpio, regla RN-01)" }
```

**Response de análisis (`GET /api/analisis/{id}`):**
```json
{
  "id_analisis": "12",
  "fecha": "2026-09-30T14:30:00Z",
  "resumen_general": {
    "nivel_riesgo_global": "alto",
    "puntaje": 85,
    "comentario_breve": "Esta política presenta 5 hallazgo(s) de riesgo alto..."
  },
  "secciones_analizadas": [
    {
      "categoria_opp115": "First Party Collection/Use",
      "titulo": "Recopilación de datos biométricos",
      "texto_original": "...",
      "hallazgos": [
        {
          "tipo": "riesgo",
          "descripcion": "Se recopilan datos biométricos sin finalidad declarada",
          "nivel": "alto",
          "criterio": "A1",
          "tipo_tratamiento": "Recopilación de datos personales",
          "sin_respaldo": false,
          "fuentes_normativas": [
            {
              "documento": "RGPD",
              "referencia": "Artículo 9",
              "fragmento_relevante": "<extracto real del fragmento del corpus, máx. 600 caracteres>",
              "jurisdiccion": "internacional"
            }
          ]
        }
      ],
      "analizada": true
    }
  ],
  "recomendaciones": ["Revisa qué permisos tiene la aplicación..."]
}
```

- `tipo`: `riesgo` | `transparencia` | `neutral`. `nivel`: `bajo` | `medio` | `alto`. Ambos se derivan de `criterio` (sección 7).
- `criterio`: código del criterio de la rúbrica (`A1`–`A10`, `M1`–`M5`, `B1`–`B4`); `null` en análisis anteriores y en la sección de respaldo.
- `analizada` (de la sección): `false` en la sección de respaldo, que no pudo analizarse; no cuenta para el nivel global ni para la puntuación. Por defecto `true` (también en análisis anteriores, que no traen el campo).
- `tipo_tratamiento`: uno de los 8 valores de la lista cerrada (sección 7); es `null` solo en análisis realizados antes de incorporar la clasificación.
- `jurisdiccion` de la fuente: `null` en análisis antiguos (el cliente y el PDF la deducen del nombre del documento).
- En la base, `resultado` incluye además `metadatos_analisis` (configuración con la que se generó; sección 7) y, tras la primera descarga del PDF, `metadatos_reporte` (sección 14). Ninguno de los dos se devuelve en la API.

### Administración — `/api/admin` (solo rol administrador)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/usuarios` | Lista paginada (`page`, `page_size` ≤ 50, `q` por nombre o correo, sin acentos) |
| `PATCH` | `/usuarios/{id}/estado` | `{activo}`; un administrador no puede desactivarse a sí mismo (400) |
| `GET` | `/corpus` | Documentos del corpus: jurisdicción, número de fragmentos, fecha de carga, estado |
| `PATCH` | `/corpus/estado` | `{documento_fuente, activo}`: activa o desactiva todos los fragmentos del documento |
| `POST` | `/corpus` | Multipart `archivo` (PDF/TXT ≤ 5 MB) + `jurisdiccion` (`guatemala`, `internacional`, `estandar_tecnico`) → 201; 5/min; `Content-Length` > 6 MB → 413 antes de leer el cuerpo |

El listado de usuarios expone solo datos de la cuenta (`id`, `nombre`, `email`, `role`, `is_active`, `created_at`), nunca el contenido de sus análisis. Ninguna ruta permite cambiar roles (ver `scripts/promover_admin.py`).

### Excepciones HTTP personalizadas

| Excepción | HTTP | Descripción |
|---|---|---|
| `CredencialesInvalidasError` | 401 | Login fallido o cuenta inactiva |
| `TokenInvalidoError` | 401 | Token expirado, inválido, revocado, anterior a `sessions_valid_from` o de una cuenta eliminada/inactiva |
| `AccesoDenegadoError` | 403 | Ruta de administración sin rol administrador |
| `UsuarioNoEncontradoError` | 404 | Usuario no existe |
| `UsuarioYaExisteError` | 409 | Email duplicado en registro |
| `AvisoNoAceptadoError` / `DeclaracionEdadFaltanteError` | 422 | Falta aceptar el aviso o la declaración de edad |
| `PasswordActualIncorrectaError` / `PasswordRepetidaError` | 400 | Cambio de contraseña rechazado |
| `PasswordIncorrectaError` | 400 | Contraseña incorrecta al eliminar la cuenta |
| `UltimoAdministradorError` | 400 | El único administrador activo no puede eliminar su cuenta |
| `AutodesactivacionError` | 400 | Un administrador intenta desactivarse |
| `CuentaConAnalisisEnCursoError` | 409 | Eliminar la cuenta con un análisis en curso |
| `TextoDemasiadoCortoError` | 422 | < 200 caracteres o < 40 palabras |
| `TextoDemasiadoLargoError` | 422 | > 300,000 caracteres; el mensaje dice cuánto mide el texto y qué hacer |
| `TextoNoEsPoliticaError` | 422 | El texto claramente no es una política de privacidad (RN-18) |
| `ConfirmacionPoliticaRequeridaError` | 422 | Texto dudoso sin `confirma_politica: true` |
| `ExtraccionURLError` | 422 | URL que no es de un sitio web público, no accesible, con demasiadas redirecciones, no HTML o sin texto |
| `ArchivoNoPermitidoError` | 415 | Archivo que no es PDF o TXT |
| `ArchivoDemasiadoGrandeError` | 413 | Archivo > 5 MB |
| `PdfSinTextoError` | 422 | PDF sin texto extraíble (escaneado) |
| `DocumentoCorpusNoEncontradoError` | 404 | Documento inexistente en el corpus |
| `DocumentoCorpusDuplicadoError` | 409 | Ya existe un documento con ese nombre de archivo |
| `DocumentoCorpusSinTextoError` | 422 | Documento con menos de 50 palabras |
| `RangoFechasInvalidoError` | 422 | `desde` posterior a `hasta` |
| `AnalisisEnCursoError` | 409 | Eliminar un análisis que se está procesando |
| `AnalisisEnProcesoError` | 409 | Consultar el detalle o el PDF de un análisis en curso |
| `AnalisisFallidoError` | 409 | Consultar el detalle o el PDF de un análisis que terminó con error |
| `AnalisisNoEncontradoError` | 404 | Análisis inexistente o ajeno |
| `LLMError` | 502 | Fallo no recuperable del proveedor del modelo |

**Formato de los errores:** todos usan `{"detail": ...}`. Los 429 llevan el mensaje en español de `manejar_limite_superado`; los 422 de validación conservan la lista de FastAPI (`manejar_validacion`), pero sin el prefijo "Value error, " que Pydantic antepone a los mensajes propios.

---

## 7. Motor de Análisis con IA

El motor se encuentra en `backend/app/services/analisis_service.py`. `POST /api/analisis/iniciar` crea el registro (`estado = procesando`), lo confirma en la base y lanza `ejecutar_analisis_background` como tarea `asyncio` del mismo proceso, con su propia sesión de base de datos. El cliente consulta `/{id}/estado` cada 1.5 s.

> **Limitación:** la tarea vive en memoria del proceso del backend; si el proceso se reinicia durante un análisis, ese análisis no continúa. Para que no quede `procesando` para siempre (y no bloquee, por ejemplo, la eliminación de la cuenta), al arrancar el servidor (`lifespan` en `app/main.py`) `marcar_analisis_interrumpidos()` pasa a `error` todos los análisis que siguen `procesando`. Si la base no está disponible al arrancar, se registra el error y el servidor inicia igual.

### Flujo completo

```
texto completo (str)
    │
    ▼
text_hash = huella_texto(texto)          (SHA-256 con los espacios normalizados)
    │  ¿Hay un análisis completado con el mismo text_hash, la misma configuración
    │  (modelo, temperatura, semilla, VERSION_PROMPT, huella del corpus) y sin
    │  secciones fallidas? → se copia su resultado y termina (sin llamar al modelo)
    │
    ▼
segmentar_politica()
    │  Divide por encabezados (numeración, romanos, markdown, líneas en mayúsculas)
    │  Descarta secciones < 30 palabras
    │  Secciones > 700 palabras → bloques de 500 palabras
    │  Texto sin encabezados → bloques de 500 palabras
    │  SIN tope de secciones: se analiza la política completa
    │
    ▼ secciones_total se guarda en la base
    │
    ├── Hasta 4 secciones en paralelo (_CONCURRENCIA_LLM = 4, asyncio.Semaphore)
    │   Cada sección (_analizar_seccion):
    │        │
    │        ▼
    │   recuperar_contexto(db, seccion, k=5, k_guatemala=2)
    │        │  5 fragmentos activos más cercanos + hasta 2 guatemaltecos (RN-07)
    │        ▼
    │   _construir_contexto_normativo()  → fragmentos numerados [Fragmento 1..n]
    │   _construir_prompt_seccion()      → sección + fragmentos (el esquema lo impone la API)
    │        ▼
    │   Llamada 1: análisis de la sección (SYSTEM_PROMPT, ESQUEMA_SECCION)
    │        │  Error transitorio tras los reintentos del adaptador → una pausa de 15 s y un último intento
    │        ▼
    │   _parsear_seccion(json, chunks, seccion)
    │        │  criterio → tipo y nivel; un solo hallazgo B por sección; texto_original = sección[:300]
    │        │  Respuesta inválida → Llamada 2: la instrucción completa + el motivo del rechazo
    │        │  Segunda respuesta inválida o LLMError → sección de respaldo (analizada = false)
    │        ▼
    │   _respaldar_hallazgos()  (segunda pasada de respaldo, si hay hallazgos sin fragmentos)
    │        ▼
    │   seccion_actual += 1 (el progreso cuenta secciones terminadas)
    │
    ▼ list[SeccionAnalizada] (en el orden original de la política)
    │
_calcular_resumen()                     → nivel global y puntuación 0–100 (sin secciones de respaldo)
_generar_recomendaciones_practicas()    → 3–5 recomendaciones
    │
    ▼
resultado (JSONB) + metadatos_analisis, text_hash, estado = completado
                                        (cualquier error no controlado → estado = error)
```

La sesión de base de datos no admite uso concurrente, así que la búsqueda en el corpus y el guardado del progreso se serializan con un `asyncio.Lock`; solo las llamadas al modelo corren en paralelo.

### Llamadas al modelo

Todas usan el mismo adaptador (sección 9), con `temperature = 0`, semilla fija (`OPENAI_SEED`) y **salidas estructuradas estrictas**: cada llamada envía su esquema JSON (`ESQUEMA_SECCION`, `ESQUEMA_RESPALDO`, `ESQUEMA_RECOMENDACIONES`) y OpenAI garantiza que la respuesta lo cumple, incluidas las listas cerradas del criterio y del tipo de tratamiento. Los textos de las instrucciones del sistema están en `analisis_service.py`; aquí se describe lo que hace cada llamada:

| Llamada | Instrucción del sistema | Cuándo | Qué pide |
|---|---|---|---|
| Análisis de sección | `SYSTEM_PROMPT` | Una por sección | Un hallazgo por cada cláusula que cumpla un criterio de la rúbrica, con el **código del criterio**, la descripción, el tipo de tratamiento y los **números** de los fragmentos que lo respaldan; además el título y la categoría OPP-115 de la sección. Define el rol (orientación a jóvenes de Guatemala), la distinción entre normativa guatemalteca y referencias internacionales, los 19 criterios con dos ejemplos y la prohibición de inventar normas o números de fragmento |
| Corrección | `SYSTEM_PROMPT` | Si la respuesta anterior no es válida | Repite la instrucción completa (sección, fragmentos y esquema) con el motivo del rechazo |
| Segunda pasada de respaldo | `SYSTEM_PROMPT_RESPALDO` | Una por sección con hallazgos sin fragmentos | Para cada hallazgo pendiente, indicar qué fragmentos (recuperados con su descripción) lo respaldan |
| Recomendaciones prácticas | `SYSTEM_PROMPT_RECOMENDACIONES` | Una al final del análisis | Redactar acciones concretas a partir de los riesgos encontrados |

### Consistencia de los resultados

El mismo texto debe producir el mismo resultado. Se combinan cuatro medidas:

1. **Criterios en lugar de niveles.** El modelo no asigna el nivel: elige el código del criterio de la rúbrica que cumple cada cláusula y el servidor deriva el nivel y el tipo con la tabla fija `CRITERIOS`:

   | Códigos | Criterios | Tipo | Nivel |
   |---|---|---|---|
   | `A1`–`A10` | Biométricos, audio o video pasivo, datos sensibles, terceros no identificados, transferencia a países sin protección, conservación indefinida, sin mecanismos de acceso, menores sin consentimiento parental, consentimiento implícito, cambios sin aviso | `riesgo` | `alto` |
   | `M1`–`M5` | Finalidades ambiguas, plazos poco claros, derechos engorrosos, transferencias con garantías genéricas, otra práctica que reduce el control del usuario | `riesgo` | `medio` |
   | `B1`–`B4` | Finalidades claras, plazos definidos, derechos con contacto identificado, aviso previo de cambios | `transparencia` | `bajo` |

   Si una cláusula cumple varios criterios se usa el de mayor nivel y se reporta un hallazgo por cláusula. Una buena práctica (B) solo se reporta en una sección **sin riesgos** (A o M), y como máximo una; el servidor aplica la misma regla y descarta las demás. Así la puntuación refleja qué parte de la política es riesgosa, sin que una buena práctica dentro de una sección con riesgos los compense. La fórmula de la puntuación (RN-05) no cambia.
2. **Generación reproducible.** `temperature = 0`, semilla fija y esquema estricto. OpenAI trata la semilla como "mejor esfuerzo": si cambia la configuración de sus servidores (`system_fingerprint`, que se registra) la respuesta puede variar.
3. **Recuperación reproducible.** La búsqueda en el corpus desempata las distancias iguales por `id`.
4. **Reutilización.** Si el texto (con los espacios normalizados) ya se analizó con la misma configuración, se copia ese resultado con el id y la fecha del análisis nuevo, sin llamar al modelo. Aplica entre usuarios distintos (solo se copia el resultado; el texto de una política es público) y nunca a un resultado con secciones fallidas. Cambiar `VERSION_PROMPT`, el modelo, la temperatura, la semilla o el corpus (cargar, activar o desactivar documentos) invalida la reutilización.

Cada resultado guarda en `metadatos_analisis` lo que hizo falta para generarlo: `modelo`, `temperatura`, `semilla`, `version_prompt`, `version_corpus` (MD5 de los ids de los fragmentos activos), `huellas_sistema` y `reutilizado_de` (id del análisis copiado o `null`). **Al modificar cualquier instrucción al modelo hay que incrementar `VERSION_PROMPT`.**

La consistencia se mide con `scripts/medir_consistencia.py` (sección 14).

### Tipo de tratamiento de datos (RN-08)

Cada hallazgo se clasifica en **uno** de 8 valores de una lista cerrada (`TIPOS_TRATAMIENTO` en `schemas/analysis.py`): Recopilación de datos personales; Uso y finalidad de los datos; Transferencia de datos a terceros; Tiempo de conservación de los datos; Seguridad de los datos; Derechos del usuario sobre sus datos; Cambios en la política; Otro. Se toleran solo diferencias de mayúsculas o espacios; cualquier otro valor invalida la respuesta y provoca la llamada de corrección. La sección de respaldo usa "Otro", lleva `analizada: false` y no cuenta para el nivel global ni para la puntuación. Los análisis anteriores a esta clasificación no tienen etiqueta (`null`) y así se muestran.

### Citas verificables (RN-06)

El modelo **no redacta citas**: solo indica números de fragmento. El servidor (`_fuente_desde_fragmento`) arma cada fuente con el fragmento real:
- `documento`: nombre del documento fuente sin extensión (`.pdf`, `.txt`, `.md`).
- `referencia`: artículos que aparecen en el texto del fragmento (hasta 3, p. ej. "Artículos 3 y 4"); vacía si no menciona ninguno.
- `fragmento_relevante`: extracto real del corpus, máximo 600 caracteres.
- `jurisdiccion`: la del fragmento en el corpus.

Los números que no corresponden a un fragmento recibido se descartan (nunca se cita algo que el modelo no vio); los repetidos se ignoran. Ya no existe la cita genérica "Principios generales de protección de datos".

### Hallazgos sin respaldo

Si ningún número de fragmento es válido, el hallazgo queda con `sin_respaldo: true`:
- Se muestra marcado en la web y en el PDF ("Sin respaldo en el corpus normativo", término también incluido en el glosario).
- **No cuenta** para el nivel global ni para la puntuación de riesgo.
- **Sí cuenta** para las recomendaciones prácticas.

### Segunda pasada de respaldo

Tras analizar una sección, sus hallazgos sin respaldo se buscan otra vez en el corpus usando **la descripción de cada hallazgo** (más precisa que la sección completa): 3 fragmentos por hallazgo (`_K_FRAGMENTOS_RESPALDO`), sin repetir. Una llamada breve (`SYSTEM_PROMPT_RESPALDO`) elige qué fragmentos respaldan cada hallazgo; los que reciben fragmentos válidos pasan a tener citas y dejan de estar sin respaldo. Si la búsqueda o la llamada fallan, la sección se conserva tal como estaba.

### Recomendaciones prácticas

`_generar_recomendaciones_practicas` hace una sola llamada al final con hasta **15** hallazgos de tipo `riesgo` y nivel alto o medio (primero los altos y, dentro de cada nivel, primero los respaldados). La respuesta debe contener entre 3 y 5 acciones en imperativo; se descartan las de más de 400 caracteres y las repetidas, y se conservan como máximo 5. Si no hay riesgos altos ni medios, o si la llamada falla o su respuesta no es válida, se usan las **recomendaciones básicas** (`_generar_recomendaciones`, sin el modelo: "En '<sección>': <hallazgo>", máximo 5, o un mensaje general si no hay hallazgos altos ni medios).

### Cálculo de la puntuación de riesgo (0–100)

En la interfaz, el panel y el PDF se denomina **"Puntuación de riesgo"** (el campo JSON conserva el nombre `puntaje`).

```python
_PESO_NIVEL = {"bajo": 1, "medio": 2, "alto": 3}

# Solo hallazgos con respaldo (sin_respaldo == False) de secciones analizadas (analizada == True)
pesos = [_PESO_NIVEL[h.nivel] for h in hallazgos_respaldados]
promedio = sum(pesos) / len(pesos)
puntaje = min(100, int((promedio - 1) / 2 * 100))

# Nivel global:
# alto    → ≥2 hallazgos alto  o  promedio >= 2.5
# medio   → ≥2 hallazgos medio o  promedio >= 1.5
# bajo    → resto (y puntaje 0 si no hay hallazgos respaldados)
```

### Mediciones de referencia

Pruebas reales registradas por el responsable el 30/09/2026 con políticas públicas (no son pruebas automatizadas):

| Política | Secciones | Hallazgos | Sin respaldo | Duración |
|---|---|---|---|---|
| Mozilla | 14 | 45 | 4 | 34,6 s |
| Spotify | 21 | 45 | 2 | 26,3 s |

Antes de las citas verificables, en esas mismas políticas solo 1 y 4 citas, respectivamente, correspondían a fragmentos reales del corpus; el resto las redactaba el modelo.

---

## 8. Arquitectura RAG y Corpus Normativo

**RAG (Retrieval-Augmented Generation)** permite que el modelo fundamente sus análisis en normativa real: recibe fragmentos numerados del corpus y solo puede citarlos por número.

### Corpus normativo

Documentos del directorio `corpus_normativo/` (el script solo toma archivos dentro de las tres carpetas de jurisdicción):

| Carpeta → jurisdicción | Documentos |
|---|---|
| `guatemala/` → `guatemala` | Constitución Política de la República de Guatemala; Decreto 57-2008 (Ley de Acceso a la Información Pública) |
| `internacional/` → `internacional` | RGPD; LOPDP España; Principios OEA 2021; Ley Modelo Parlatino 2022 |
| `estandares_tecnicos/` → `estandar_tecnico` | El Corpus OPP-115 y su Ontología Estructural; Metodología, Casuística y Algoritmos del Proyecto ToS;DR (PDF y `tosdr_metodologia.md`) |

Los administradores pueden agregar documentos desde `/admin/corpus` y activar o desactivar documentos completos. **Solo los fragmentos activos** participan en la recuperación; desactivar no modifica el texto ni los embeddings.

Los **Principios OEA 2021** se cargan desde `internacional/Principios OEA 2021.txt`: el PDF oficial está maquetado en pliegos con texto a dos columnas y su extracción directa mezclaba las columnas, así que el TXT se obtuvo de ese mismo PDF extrayendo cada página del libro por separado, uniendo las palabras cortadas con guion y quitando números de página y encabezados repetidos. El PDF original se conserva en `corpus_normativo/originales/`, que el script no carga (detalle en `corpus_normativo/README.md`).

### Modelo de embeddings

```
Modelo: paraphrase-multilingual-mpnet-base-v2 (sentence-transformers)
Dimensión: 768
Normalización: L2 (la similitud coseno equivale al producto punto)
Carga: diferida, una sola vez por proceso; caché en backend/.model_cache
Ejecución: en un hilo aparte (asyncio.to_thread / threadpool) para no bloquear el event loop
```

### Segmentación del corpus (`utils/chunking.py`)

Por párrafos (y por oraciones si un párrafo supera el máximo): objetivo 400 palabras, máximo 500, solapamiento de 50 palabras entre fragmentos consecutivos y mínimo 50 palabras por fragmento. Cada fragmento lleva en `metadatos.hash` el MD5 de `documento::texto`, que evita duplicados.

### Carga del corpus

**Por script** (ver sección 14): `scripts/cargar_corpus.py` recorre `guatemala/`, `internacional/` y `estandares_tecnicos/` (archivos `.pdf`, `.txt`, `.md`), ignora los que tengan menos de 50 palabras y es **idempotente**: los fragmentos cuyo hash ya existe no se vuelven a insertar.

**Desde la administración** (`POST /api/admin/corpus`): PDF o TXT de hasta 5 MB y jurisdicción elegida; como cada carga genera embeddings, se admiten como máximo 5 por minuto, y un envío con `Content-Length` mayor de 6 MB se rechaza con 413 antes de leerlo. El **nombre del archivo es el identificador del documento**: si ya existe un documento con ese nombre, responde **409**. Se reutiliza el mismo proceso de segmentación, embeddings y deduplicación del script; el archivo original se descarta y solo se conservan los fragmentos.

### Búsqueda vectorial

```sql
-- Operador <=> = distancia coseno (pgvector); menor valor = mayor similitud
SELECT id, documento_fuente, jurisdiccion, referencia,
       categoria_tematica, texto_original, metadatos
FROM   corpus_chunks
WHERE  active = true [AND jurisdiccion = :jurisdiccion]
ORDER  BY embedding <=> CAST(:embedding AS vector)
LIMIT  :k
```

- **Búsqueda exacta:** la migración 0008 elimina el índice aproximado ivfflat, que se creaba con la tabla vacía (sus listas no representaban el corpus) y reducía la precisión. Con el tamaño actual del corpus (cientos de fragmentos) la búsqueda exacta tarda milisegundos. Si el corpus llegara a decenas de miles de fragmentos, conviene crear un índice nuevo **después** de cargar los datos (el `downgrade` de 0008 muestra la sentencia).
- **Normativa guatemalteca (RN-07):** cada sección recibe los 5 fragmentos más cercanos (`_K_FRAGMENTOS`) más los 2 fragmentos guatemaltecos más cercanos (`_K_GUATEMALA`) que no estén ya entre esos 5; sin ellos, el modelo casi nunca podía citar normativa nacional.

### Jurisdicción de una cita

Las citas nuevas guardan la jurisdicción del fragmento del corpus. Para los análisis anteriores (sin ese dato), la jurisdicción se deduce del nombre del documento con las **mismas claves** en `frontend/src/utils/jurisdiccion.ts` y en `reportes_service._inferir_jurisdiccion` (por ejemplo, Decreto 57-2008 → Guatemala; ToS;DR y OPP → estándar técnico; el resto → internacional). Si se agregan documentos con nombres nuevos y hay que clasificar análisis antiguos, se deben ampliar las claves en ambos archivos.

---

## 9. Adaptadores LLM

El sistema implementa el **patrón Adapter** para poder sustituir el proveedor del modelo sin modificar el motor de análisis. **OpenAI es el único proveedor** implementado.

### Interfaz base (`services/llm/base.py`)

```python
class LLMAdapter(ABC):
    @abstractmethod
    async def generar_analisis(
        self,
        system_prompt: str,
        texto_seccion: str,
        contexto_normativo: str,
    ) -> str:  # JSON string
        ...
```

### Selección del adaptador

`analisis_service._crear_adaptador_llm()` actúa como fábrica: lee `LLM_PROVIDER` y, con el valor `openai` (el único admitido), crea `OpenAIAdapter` con `OPENAI_API_KEY` y `OPENAI_MODEL`. Cualquier otro valor produce un error. Para incorporar otro proveedor bastaría con un nuevo adaptador y una rama en esa fábrica.

### OpenAI Adapter (`services/llm/openai_adapter.py`)

```python
# Configuración
Modelo: OPENAI_MODEL (por defecto gpt-4o-mini)
Temperature: OPENAI_TEMPERATURE (por defecto 0)
Seed: OPENAI_SEED (por defecto 20261003; "mejor esfuerzo" según OpenAI)
response_format: {"type": "json_schema", "json_schema": {..., "strict": true}}  # si la llamada envía esquema
                 {"type": "json_object"}                                      # si no lo envía
huellas_sistema: system_fingerprint de cada respuesta (se guardan en metadatos_analisis)
Mensajes: system (instrucción) + user (prompt completo construido por el motor)

# Reintentos (tenacity)
Intentos: 3
Espera: exponencial, entre 2 s y 10 s
Reintenta en: RateLimitError (429), APIConnectionError y errores 5xx
No reintenta en: otros 4xx (autenticación, modelo inválido) → LLMError (502)
```

La clave de API se lee solo de la configuración y nunca se escribe en los registros.

---

## 10. Frontend — Interfaz de Usuario

### Rutas

| Página | Ruta | Acceso | Descripción |
|---|---|---|---|
| Login | `/login` | Pública | Inicio de sesión |
| Register | `/registro` | Pública | Registro con aceptación del aviso y declaración de edad |
| AvisoPrivacidad | `/aviso-privacidad` | Pública | Aviso de privacidad de PrivApp |
| Glosario | `/glosario` | Pública | Glosario con búsqueda sin acentos |
| Dashboard | `/dashboard` (`/` redirige aquí) | Autenticada | Accesos y panel estadístico |
| Ingesta | `/analizar` | Autenticada | Texto, URL o archivo, con vista previa |
| Resultados | `/resultados/:id` | Autenticada | Progreso y resultado del análisis |
| Historial | `/historial` | Autenticada | Lista paginada con filtros y eliminación |
| Perfil | `/perfil` | Autenticada | Nombre, contraseña y eliminación de la cuenta |
| Admin | `/admin` | Administrador | Menú de administración |
| AdminUsuarios | `/admin/usuarios` | Administrador | Búsqueda y activación/desactivación de cuentas |
| AdminCorpus | `/admin/corpus` | Administrador | Documentos del corpus: carga y activación |

`ProtectedRoute` exige sesión; `AdminRoute` además exige el rol administrador. Estas guardas solo ocultan la navegación: **el servidor verifica el rol en cada ruta administrativa**. El pie de página enlaza el glosario y el aviso de privacidad en todas las pantallas.

### Estructura y navegación

- `LayoutPublico` (`/login`, `/registro`): contenido, interruptor del tema y pie de página.
- `AppLayout` (todas las demás): enlace "Saltar al contenido", barra superior (`Navbar`), la página, el pie de página y, **con sesión**, las pestañas inferiores del celular (`BarraPestanas`, ocultas desde `md`). Cada página aporta su propio `<main>`.
- Los destinos principales están definidos una sola vez en `components/layout/secciones.ts`: Inicio, Analizar (también activa en `/resultados/:id`), Historial, Glosario y Perfil. La barra superior muestra Inicio, Analizar e Historial desde `md`; Glosario, Perfil (con el nombre), Administración (solo el administrador), el interruptor del tema y Cerrar sesión van a la derecha. La sección actual lleva `aria-current="page"`.
- Cualquier ruta que no existe muestra `NoEncontrada` ("Página no encontrada", con enlaces al inicio y al glosario) dentro de `AppLayout`.
- Inicio de sesión y registro abren con `Bienvenida` (logotipo, título y subtítulo).

### Tema claro y oscuro

- Los colores son **tokens** (variables CSS en canales RGB) definidos en `src/index.css` para `:root` (claro) y `.dark` (oscuro), y expuestos en `tailwind.config.js` como `fondo`, `superficie`, `superficie-2`, `texto`, `texto-2`, `texto-3`, `borde`, `borde-fuerte`, `marca` (`hover`, `texto`, `suave`, `suave-texto`, `borde`), `riesgo` (`alto`, `medio`, `bajo` y sus `-solido`) y `juri`. Con `rgb(var(--…) / <alpha-value>)` admiten opacidad (`bg-riesgo-alto/10`). **No usar la paleta fija de Tailwind** (`gray-*`, `blue-*`…): cada clase de token funciona en ambos modos sin escribir variantes `dark:`.
- Todos los pares de texto y fondo cumplen el contraste AA (4.5:1). El nivel de riesgo nunca se comunica solo con color: lleva texto e icono.
- `TemaProvider` (`context/TemaContext.tsx`) guarda la preferencia en `localStorage` (`privapp-tema`: `claro` u `oscuro`; sin valor, sigue `prefers-color-scheme` del dispositivo y sus cambios) y pone o quita la clase `dark` en `<html>`. Un script en línea de `index.html` aplica el tema antes del primer pintado para evitar un destello claro; usa la misma clave. `BotonTema` (sol/luna, `aria-pressed`) alterna el modo. En Mi perfil, `Apariencia` ofrece Claro, Oscuro o Automático (este último borra la preferencia guardada).
- La fuente Figtree se sirve desde el propio sitio (`public/fonts/`, licencia en `OFL.txt`) y no desde Google Fonts, para no enviar a un tercero la IP de cada visitante.

### Componentes comunes (`components/common/`)

| Componente | Uso |
|---|---|
| `Button` | Variantes `primary`, `secondary`, `ghost` y `danger`; `type="button"` por defecto |
| `Input`, `CampoSeleccion`, `AreaTexto`, `Casilla` (`Campos.tsx`) | Campo con etiqueta asociada, ayuda (`aria-describedby`) y error (`aria-invalid`) |
| `Aviso` | Mensaje de error (`role="alert"`), éxito o información (`role="status"`) |
| `Cargando`, `Spinner` | Tarjeta de carga con mensaje; el spinner solo es accesible si lleva `etiqueta` |
| `EstadoVacio` | Lista o pantalla sin contenido, con una acción sugerida |
| `EncabezadoPagina` | Título, subtítulo, botón de volver y acciones |
| `Insignia` | Etiqueta breve con tono (`alto`, `medio`, `bajo`, `marca`, `neutro`, `juri`) |
| `Paginacion` | Anterior / "Página X de Y" / Siguiente |
| `DialogoConfirmacion` | `Dialog` de Headless UI con `role="alertdialog"`: retiene el foco, empieza en Cancelar y Escape cancela (salvo mientras procesa) |

Los botones, enlaces de navegación y campos tienen al menos 44 px de alto, y todo elemento interactivo muestra el foco con un contorno del color de marca.

### Ingesta y vista previa

`IngestaForm` muestra los pasos del análisis ("Pega o sube", "Revisa el texto", "Resultados"; el actual con `aria-current="step"`) y tres pestañas (pegar texto, desde URL, desde archivo; el archivo se elige en una zona de carga). Aplica en el cliente la misma regla RN-01 (`utils/validators.ts`: 200 caracteres, 40 palabras, máx. 300,000) y la validación de archivo (.pdf/.txt, ≤ 5 MB, no vacío), pero la regla definitiva la aplica el servidor. Tras la ingesta se muestra `VistaPreviaTexto` con el texto extraído, caracteres y palabras; el análisis **solo se inicia al confirmar** la vista previa (también se puede corregir o cancelar). Si la detección considera el texto dudoso, la vista previa muestra los temas encontrados y el botón de analizar se habilita solo al marcar "Confirmo que este texto es una política de privacidad..."; entonces envía `confirma_politica: true`. Si el análisis termina con el motivo `no_es_politica`, la pantalla de resultados lo explica en lugar de mostrar un error genérico.

### Progreso y resultados

- `useProgresoAnalisis` consulta `/{id}/estado` cada 1.5 s; `VistaProgreso` muestra las secciones terminadas y rota consejos de privacidad (`data/consejosPrivacidad.ts`) cada 6 s.
- **Disposición:** en el celular, una sola columna; desde `lg`, el resumen queda fijo a la izquierda (puntuación, "¿Por qué este resultado?" y acciones) y el detalle a la derecha ("Qué hace con tus datos", hallazgos, recomendaciones y aviso).
- **MedidorRiesgo:** semicírculo de 0 a 100 con las franjas de la RN-05 (bajo < 25, medio < 75, alto) y la aguja en la puntuación; su nombre accesible es "Puntuación de riesgo: N de 100, Riesgo X".
- **InsigniaNivel:** nivel con icono y texto ("Riesgo alto", "Riesgo medio", "Riesgo bajo"; "Buena práctica" para los hallazgos de transparencia): nunca solo color.
- **PorQueResultado:** cuántas cláusulas cuentan para el resultado (secciones analizadas y con respaldo, `utils/resumenResultados.ts`), barras por nivel y la regla que decide el nivel general, la misma del servidor (`explicarNivel`).
- **ResumenTratamiento** ("Qué hace con tus datos"): una ficha por tipo de tratamiento con sus riesgos ("6 altos · 2 medios"), de la que tiene más riesgos altos a la que menos; al pulsarla, la lista de hallazgos se filtra por ese tipo.
- **TarjetaSeccion:** secciones plegables; cada hallazgo muestra nivel, tipo de tratamiento, la descripción, **"Por qué"** (el criterio de la rúbrica en lenguaje sencillo, `data/criterios.ts`; solo en análisis con `criterio`), la marca de "sin respaldo" y, desplegables, las normas que lo respaldan y el fragmento analizado.
- **CitaNormativa:** documento, referencia, extracto real y jurisdicción de cada cita.
- **FiltroHallazgos:** filtra por nivel, por jurisdicción de la cita y por tipo de tratamiento, **solo en el cliente**; las secciones sin coincidencias se ocultan y las visibles conservan su número original; el resumen general no cambia.
- **ListaRecomendaciones** ("Qué puedes hacer"): recomendaciones prácticas como tarjetas numeradas.
- **AyudaGlosario:** ayuda contextual que muestra la definición de un término del glosario.
- Descarga del PDF y eliminación del análisis con confirmación (`DialogoConfirmacion`).

### Historial

Los análisis se muestran como tarjetas agrupadas por día ("Hoy", "Ayer" o la fecha), con un anillo de la puntuación y el nivel con texto. `FormFiltrosHistorial`: texto, nivel y rango de fechas. Las fechas se eligen como días locales y `limiteDelDia` (`api/analisis.ts`) las convierte en el instante UTC de inicio (00:00:00.000) o de fin (23:59:59.999) de ese día antes de enviarlas. La búsqueda no distingue acentos. Cada análisis puede eliminarse con confirmación.

### Panel estadístico

El inicio (`/dashboard`) da la bienvenida y ofrece accesos a Analizar política, Mis análisis y Glosario. `PanelEstadistico` consulta `GET /api/analisis/estadisticas` y muestra el total de análisis, la puntuación de riesgo promedio y la distribución por nivel. El gráfico (`GraficoDistribucion`, con **recharts**) se carga de forma diferida con `React.lazy` + `Suspense` y solo cuando hay análisis que graficar, de modo que recharts queda en un archivo aparte y no se descarga en el resto de las pantallas.

### Glosario y aviso de privacidad

- Contenido del glosario (22 términos aprobados): `frontend/src/data/glosario.ts`. La página los muestra como tarjetas en columnas (una, dos o tres según el ancho) con buscador; cada tarjeta conserva el `id` del término para los enlaces `/glosario#termino`.
- El aviso de privacidad tiene un índice de sus apartados al inicio.
- Contenido del aviso de privacidad: `frontend/src/data/avisoPrivacidad.ts`. La función `datosPendientes()` lista los marcadores entre corchetes (`[...]`) que aún faltan por completar. Si cambia el funcionamiento del sistema (datos tratados, proveedores, plazos), hay que revisar el aviso.

### Autenticación en el cliente

```typescript
// AuthContext.tsx / api/client.ts
// - JWT almacenado en localStorage ('access_token')
// - Interceptor axios: agrega Authorization: Bearer <token> a cada solicitud
// - Respuesta 401: borra el token y redirige a /login
// - Cambio de contraseña: guarda el token nuevo que devuelve el servidor
// - Eliminar cuenta / logout: olvida el token en el navegador
```

`VITE_API_URL` define la URL del backend (por defecto `http://localhost:8000`); en desarrollo Vite además redirige `/api` al servicio `backend`. En la imagen de producción es obligatoria y se fija al construirla (ver sección 14).

---

## 11. Cuentas, Sesiones y Roles

### Tokens

```
Algoritmo: HS256 — secreto JWT_SECRET_KEY
Expiración: JWT_EXPIRATION_HOURS (24 h por defecto)
Payload: { "sub": "<user_id>", "role": "<rol>", "iat": <segundos con fracción>,
           "exp": <timestamp>, "jti": "<uuid4>" }
```

- `iat` se emite con fracción de segundo para compararlo sin ambigüedad con `users.sessions_valid_from`.
- `role` viaja solo como dato informativo para el cliente.

### Validación en cada solicitud (`api/deps.py`)

1. Firma y expiración válidas.
2. El `jti` no está revocado en Redis.
3. El usuario existe y está activo (un token de una cuenta eliminada o desactivada → 401).
4. El token es posterior a `sessions_valid_from` (un token sin `iat` se rechaza si ese campo tiene valor).

### Revocación e invalidación de sesiones

| Acción | Efecto |
|---|---|
| Cerrar sesión (`POST /logout`) | El `jti` se guarda en Redis (`revoked_jti:<jti>`) con un TTL igual al tiempo restante del token; la lista se limpia sola |
| Cambiar contraseña | `sessions_valid_from = ahora`: se invalidan **todas** las sesiones y se devuelve un token nuevo para la sesión actual |
| Desactivar una cuenta (administrador) | `sessions_valid_from = ahora` y el inicio de sesión queda rechazado |
| Eliminar la cuenta | La cuenta deja de existir (sus tokens → 401) y el token actual se revoca explícitamente |

El estado de revocación vive en Redis (compartido entre instancias), no en memoria del proceso.

### Roles y administración

- Roles: `usuario` (por defecto) y `administrador`.
- La autorización (`require_admin`) usa el **rol vigente en la base de datos**, no el del token: un cambio de rol tiene efecto inmediato en el servidor.
- El rol administrador solo se asigna con `scripts/promover_admin.py` (sección 14); ninguna ruta de la API eleva roles. Tras la promoción, la persona debe volver a iniciar sesión para que su token (y por tanto la interfaz) refleje el rol.
- Un administrador no puede desactivarse a sí mismo, y el único administrador activo no puede eliminar su cuenta.

### Eliminación de la cuenta

`DELETE /api/auth/me` con `{password}` (5/min): eliminación **definitiva** de la cuenta y de todos sus análisis (se borran explícitamente, sin depender del `ON DELETE CASCADE`) → 204. Errores: 400 contraseña incorrecta o único administrador activo; 409 si hay un análisis en curso. En el cliente, la sección "Eliminar mi cuenta" del perfil (`FormEliminarCuenta`) pide la contraseña y una confirmación.

---

## 12. Privacidad del Propio Sistema

### Aviso de privacidad y declaración de edad

- El registro exige dos casillas: aceptación del aviso de privacidad (`acepta_aviso`) y declaración de ser mayor de 18 años o contar con el consentimiento de la madre, el padre o la persona encargada (`declara_edad`). Se validan en el esquema y otra vez en el servicio.
- Se guardan las fechas en `users.privacy_accepted_at` y `users.age_declaration_at` (esta última nula en cuentas anteriores a la migración 0009).
- El aviso es una página pública (`/aviso-privacidad`); su contenido está en `frontend/src/data/avisoPrivacidad.ts`.

### Minimización de datos

- De cada política solo se guardan los primeros 2,000 caracteres; los archivos cargados se procesan en memoria y se descartan.
- El listado de administración de usuarios no muestra el contenido de los análisis.
- La eliminación de análisis y de la cuenta es definitiva.

### Registros sin datos personales (`app/core/registro.py`)

- Los mensajes propios del servidor no incluyen correos, nombres de archivos cargados por el usuario ni direcciones web completas: de una URL solo se registra el nombre del sitio; los usuarios se identifican por su `id`.
- SlowAPI escribe la IP al rechazar una solicitud por exceso; el filtro `OcultarIpLimitador` la reemplaza por `[ip omitida]`.
- En producción el registro de acceso de Uvicorn (una línea con la IP por solicitud) se desactiva con `--no-access-log` (CMD del Dockerfile). La plataforma de alojamiento (Railway) recibe la IP en su propia capa, fuera del control de la aplicación (lo indica el aviso de privacidad).
- SQLAlchemy solo registra las sentencias SQL con sus parámetros (`echo`), que pueden incluir el correo de una consulta, si `SQL_ECHO=true`. Está apagado por defecto y ya no depende de `ENVIRONMENT`; se activa solo para depurar en local, nunca en producción.

---

## 13. Seguridad

### Contraseñas

```
Hash: bcrypt (passlib[bcrypt] 1.7.4 + bcrypt 3.2.2)
Nunca se almacena ni se registra la contraseña en texto plano
Operaciones sensibles (cambio de contraseña, eliminar cuenta) piden la contraseña vigente
```

### Límite de solicitudes

```
Implementación: SlowAPI (SlowAPIMiddleware)
Clave: dirección IP del cliente (con --proxy-headers, la que informa el proxy)
Contador: en memoria (por proceso)
Límites: ver sección 6
```

### Cargas de archivo

- Validación de extensión, tipo de contenido y firma `%PDF-`.
- Rechazo temprano por `Content-Length` (> 6 MB → 413) en los `POST` a `/api/ingesta/archivo` y `/api/admin/corpus` (`RUTAS_CARGA_ARCHIVO` en `app/core/limite_carga.py`) y lectura limitada a 5 MB + 1 byte en las dos rutas.
- Procesamiento solo en memoria (sin archivos temporales para cargas válidas).

### Ingesta por URL

Solo se descargan sitios web públicos: `http`/`https`, puertos estándar, sin credenciales en la URL y con un nombre que resuelva solo a IP públicas; las redirecciones se siguen a mano (máximo 5) validando cada destino (sección 6). Evita que el servidor se use para consultar servicios internos (SSRF).

### CORS

```
Orígenes permitidos: CORS_ORIGINS (lista separada por comas)
Desarrollo: http://localhost:5173
Producción: dominio real del frontend
```

### Consideraciones de producción

- El archivo `.env` nunca se versiona (en `.gitignore`); `.env.example` solo contiene marcadores.
- Las claves de API se leen exclusivamente de variables de entorno y no se registran.
- Todas las rutas de ingesta, análisis y perfil requieren un token válido; las de administración, además, el rol administrador.
- Autorización por rol vigente en la base de datos y revocación de tokens en Redis (sección 11).

---

## 14. Configuración, Despliegue y Scripts

### Requisitos previos

- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Docker Compose v2+
- Git
- Una clave de API de OpenAI

### Primer despliegue (entorno local)

```bash
# 1. Clonar el repositorio
git clone <url-repo>
cd PrivApp

# 2. Crear archivo de entorno y completar los valores
cp .env.example .env
#    El REDIS_URL de .env.example (redis://redis:6379/0) ya apunta al servicio
#    redis de Docker Compose; en Railway se usa la URL de su servicio de Redis.

# 3. Construir e iniciar los servicios
docker compose up --build

# 4. Aplicar migraciones
docker compose exec backend alembic upgrade head

# 5. Cargar el corpus normativo
docker compose exec backend python scripts/cargar_corpus.py

# 6. (Opcional) Promover a un administrador (debe estar registrado)
docker compose exec backend python scripts/promover_admin.py <correo>

# 7. Verificar
docker compose exec backend pytest
```

### Arranque: desarrollo y producción

| | Desarrollo (`docker-compose.yml`) | Producción (CMD de `backend/Dockerfile`) |
|---|---|---|
| Recarga automática | `--reload` sobre el código montado | No |
| Registro de acceso | Activo | `--no-access-log` |
| Cabeceras del proxy | `--proxy-headers --forwarded-allow-ips=*` | `--proxy-headers --forwarded-allow-ips=*` |

`--forwarded-allow-ips="*"` se usa porque Railway no publica direcciones IP fijas para su proxy; así Uvicorn toma la IP real del cliente de las cabeceras reenviadas (necesaria para el límite de solicitudes por IP). La imagen del backend instala torch en su variante solo CPU antes del resto de dependencias.

El `frontend/Dockerfile` tiene tres etapas:

| Etapa | Uso | Qué hace |
|---|---|---|
| `desarrollo` | `docker-compose.yml` (`target: desarrollo`) | Servidor de Vite con recarga automática en el puerto 5173 |
| `construccion` | Intermedia | `npm ci` y `npm run build`; exige el argumento `VITE_API_URL` y falla si falta |
| `produccion` | Por defecto (Railway) | nginx sirve `dist/` en el puerto `PORT` (80 si no se define) |

Vite incrusta `VITE_API_URL` en los archivos generados, así que en producción se fija **al construir** la imagen, no al arrancarla: en Railway basta con definir la variable `VITE_API_URL` (URL pública del backend, con `https://`) en el servicio del frontend, y si cambia hay que volver a desplegarlo. nginx (`frontend/nginx/default.conf.template`) devuelve `index.html` para cualquier ruta desconocida, para que React Router resuelva rutas como `/resultados/12` al recargar la página; los archivos de `/assets/` llevan caché larga porque su nombre incluye un hash, e `index.html` se sirve sin caché para que cada despliegue se vea de inmediato.

Para probar la imagen de producción en local:

```bash
docker build -t privapp-frontend-prod --build-arg VITE_API_URL=http://localhost:8000 frontend
docker run --rm -p 5173:80 privapp-frontend-prod   # http://localhost:5173, con el backend de Compose
```

### Servicios disponibles (entorno local)

| Servicio | URL | Descripción |
|---|---|---|
| Frontend | http://localhost:5173 | Aplicación web |
| Backend API | http://localhost:8000 | REST API |
| Documentación API | http://localhost:8000/docs | Swagger UI |
| Health check | http://localhost:8000/health | Estado del servicio |
| PostgreSQL | localhost:5432 | Base de datos |
| Redis | localhost:6379 | Revocación de tokens |

### Scripts de operación (`backend/scripts/`)

**Carga del corpus — `cargar_corpus.py`**
```bash
docker compose exec backend python scripts/cargar_corpus.py
docker compose exec backend python scripts/cargar_corpus.py --limpiar   # vacía corpus_chunks (pide confirmación)
```
Lee `/app/corpus_normativo/` (docker-compose monta `./corpus_normativo` en solo lectura); solo procesa archivos dentro de `guatemala/`, `internacional/` y `estandares_tecnicos/`, lo que excluye el README, otras notas y `originales/`. Es idempotente (deduplicación por hash) y al final imprime documentos procesados, fragmentos insertados y duplicados, archivos saltados y errores. Requiere que la tabla exista (`alembic upgrade head`). Como alternativa, los documentos se pueden cargar desde `/admin/corpus` (PDF/TXT ≤ 5 MB; el nombre del archivo es el identificador; un nombre repetido → 409).

**Promover administrador — `promover_admin.py`**
```bash
docker compose exec backend python scripts/promover_admin.py <correo>
```
Asigna el rol `administrador` a un usuario ya registrado (única vía para hacerlo). El servidor reconoce el rol de inmediato, pero la persona debe volver a iniciar sesión para que su token lo lleve y la interfaz muestre el menú de administración.

**Tiempos del reporte PDF — `tiempos_reporte.py`**
```bash
docker compose exec backend python scripts/tiempos_reporte.py
docker compose exec backend python scripts/tiempos_reporte.py --detalle   # además, tiempo por análisis
```
Cada descarga del PDF mide el tiempo de construcción del documento y lo registra en `resultado.metadatos_reporte` del análisis (última generación, total de generaciones y las **últimas 10 mediciones**); si el registro falla, la descarga no se interrumpe. El script muestra promedio, mediana, mínimo, máximo y percentil 95 (método del rango más cercano) de todas las mediciones guardadas. No existe ninguna ruta de la API para estos datos.

**Consistencia del análisis — `medir_consistencia.py`**
```bash
# Credenciales de una cuenta ya registrada, en variables de entorno (no en la línea de comandos)
docker compose exec -e PRIVAPP_CORREO -e PRIVAPP_PASSWORD backend \
    python scripts/medir_consistencia.py --url-politica https://... --archivo /tmp/politica.txt --repeticiones 0
docker compose exec -e PRIVAPP_CORREO -e PRIVAPP_PASSWORD backend \
    python scripts/medir_consistencia.py --archivo /tmp/politica.txt --repeticiones 5 --sin-reutilizacion --salida /tmp/medicion.json
```
Analiza varias veces el mismo texto mediante la API (respetando el límite de 5 análisis por minuto) y compara puntuación (promedio, desviación y rango), nivel general, hallazgos que cuentan por nivel, secciones con los mismos niveles en todas las ejecuciones y similitud de las recomendaciones. Con `--sin-reutilizacion` elimina cada análisis al terminar para que el siguiente se calcule de nuevo y así medir al modelo; sin esa opción, a partir de la segunda ejecución se reutiliza el resultado. Cada ejecución consume llamadas reales a OpenAI. `--repeticiones 0` solo descarga y guarda el texto.

**Detección de políticas — `evaluar_deteccion.py`**
```bash
docker compose exec backend python scripts/evaluar_deteccion.py /tmp/conjunto
```
Evalúa la detección de políticas de privacidad (RN-18) con una carpeta de textos `.txt` cuyo nombre empieza por la etiqueta esperada: `politica_*` (deben pasar), `parecido_*` (términos de servicio, avisos de cookies: no deben rechazarse) y `no_politica_*` (deben rechazarse). Muestra por archivo los temas, la cobertura semántica, la voz del responsable y la decisión, y los aciertos por grupo. Sirve para recalibrar los umbrales de `services/deteccion_politica.py` si se cambian los temas o los prototipos.

### Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f backend

# Reiniciar solo el backend
docker compose restart backend

# Reconstruir backend (cambios en requirements.txt o Dockerfile)
docker compose build backend && docker compose up backend -d

# Acceder a PostgreSQL (usuario y base definidos en .env)
docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB>

# Fragmentos por documento del corpus
docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB> \
  -c "SELECT documento_fuente, jurisdiccion, COUNT(*), BOOL_AND(active) FROM corpus_chunks GROUP BY 1, 2 ORDER BY 2, 1;"
```

### Reconstrucción completa (elimina datos)

```bash
docker compose down -v          # elimina contenedores y volúmenes
docker compose up --build       # reconstruye desde cero (luego migraciones y corpus)
```

---

## 15. Pruebas Automatizadas

### Backend (pytest)

```bash
docker compose exec backend pytest
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

Última ejecución (01/10/2026): **408 pruebas aprobadas y 16 omitidas** sin `PRIVAPP_TEST_PG_URL` (las omitidas son las de integración contra PostgreSQL); con esa variable definida, 421 aprobadas y 1 omitida.

**Infraestructura (`tests/conftest.py`):**
- SQLite en memoria (`sqlite+aiosqlite:///:memory:`) con `StaticPool`, para que la tarea de fondo del análisis vea la misma base que la solicitud. Solo se crean `users` y `analysis_temp` (pgvector no existe en SQLite).
- `FakeRedis` sustituye a Redis en todas las pruebas; el limitador de solicitudes se reinicia antes y después de cada prueba.
- `seed_user` crea el usuario de prueba con `id=1`; `client` es un `AsyncClient` con la sesión de prueba inyectada.
- En SQLite se registra una función `sin_acentos` equivalente a `unaccent`, y `JSONBCompat` guarda el JSON como texto.

| Archivo | Qué prueba |
|---|---|
| `test_auth.py`, `test_sesiones.py`, `test_roles.py` | Registro, login, rutas protegidas, revocación, `sessions_valid_from`, autorización por rol |
| `test_perfil.py`, `test_cambio_password.py`, `test_eliminar_cuenta.py` | Perfil, cambio de contraseña, eliminación de cuenta |
| `test_aviso_privacidad.py` | Aceptación del aviso y declaración de edad |
| `test_admin_usuarios.py`, `test_admin_corpus.py` | Administración de usuarios y del corpus |
| `test_ingesta.py`, `test_carga_archivo.py`, `test_validacion_longitud.py` | Limpieza, URL, archivos PDF/TXT, regla RN-01 |
| `test_url_publica.py` | Ingesta por URL solo de sitios públicos: esquema, puerto, credenciales, IP y redirecciones |
| `test_email_minusculas.py` | Registro e inicio de sesión sin distinguir mayúsculas en el correo |
| `test_coherencia_resultados.py` | Secciones no analizadas fuera del resumen, análisis interrumpidos, 409 del detalle y del PDF, formato de 429 y 422, versión |
| `test_analisis.py` | Segmentación, parseo, tipo de tratamiento, citas, sin respaldo, segunda pasada, recomendaciones, resumen, endpoints |
| `test_rag.py` | Chunking, metadatos, extracción de PDF, embeddings, recuperación |
| `test_llm_adapters.py` | Política de reintentos del adaptador de OpenAI |
| `test_historial_filtros.py`, `test_estadisticas.py`, `test_eliminacion_analisis.py` | Historial, panel, eliminación |
| `test_reportes.py`, `test_tiempo_reporte.py` | Reporte PDF y medición de tiempos |
| `test_registro_sin_datos_personales.py` | Registros sin correos, archivos, URL completas ni IP |

**Integración contra PostgreSQL (`tests/integracion/`):** prueban pgvector, JSONB y `unaccent` (corpus e historial). Se ejecutan solo si `PRIVAPP_TEST_PG_URL` apunta a una base PostgreSQL con pgvector y las migraciones aplicadas:

```bash
PRIVAPP_TEST_PG_URL=postgresql+asyncpg://<usuario>:<clave>@<host>:5432/<base_de_pruebas> pytest tests/integracion
```

> **Advertencia:** estas pruebas vacían las tablas que usan (`TRUNCATE`). **Nunca** deben apuntar a una base con datos reales.

### Frontend (Vitest)

```bash
cd frontend
npm test              # modo observación
npx vitest run        # una sola ejecución
```

Vitest con entorno **jsdom**, Testing Library y `src/test/setup.ts`. Las pruebas están junto al archivo que prueban (`*.test.ts` / `*.test.tsx`) y cubren la mayoría de componentes, páginas, hooks, clientes de API, utilidades y archivos de datos. Si el frontend corre en Docker: `docker compose exec frontend npx vitest run`.

### Nota sobre el entorno de desarrollo

En Docker Desktop con WSL2, el reloj del contenedor puede retroceder unos 32 s cada 30 s. Si una prueba de sesiones falla de forma aislada, repita la suite (y considere ejecutar `wsl --update`).

---

## 16. Historial de Sprints

| Sprint | Commit | Descripción |
|---|---|---|
| Sprint 1 | `d1e74f7` | Módulo de autenticación completo (registro, login, JWT, rutas protegidas) |
| Sprint 2 | `8f8fd82` | Corpus normativo y arquitectura RAG (chunking, embeddings, pgvector) |
| Sprint 3 | `91f6043` | Ingesta de políticas (texto directo, extracción URL, adaptador LLM) |
| Sprint 4 | `06d3a40` | Motor de análisis (RAG + LLM + endpoints + visualización básica) |
| Sprint 5 | `48a569e` | Panel de visualización mobile-first (semáforo, secciones, citas normativas) |
| Sprint 6 | `dc5468e` | Documentación final del prototipo v1.0 |
| v1.0 | `e98e50a` | Release oficial del prototipo |
| Sprint 7 | `27cccac` | Migración a OpenAI, límite 200k chars, pruebas corregidas |
| Proyecto de Graduación II | rama `develop` | Roles, sesiones revocables, aviso de privacidad, perfil y eliminación de cuenta, administración, carga de archivos, análisis completo en paralelo, citas verificables, recomendaciones prácticas, historial con filtros, panel estadístico, glosario, migraciones 0004–0010, Vitest (detalle en `CHANGELOG.md`) |

---

## 17. Variables de Entorno

Archivo `.env` (nunca versionar). Mismos nombres que `.env.example`:

```bash
# Base de datos
POSTGRES_USER=<usuario>
POSTGRES_PASSWORD=<contraseña-segura>
POSTGRES_DB=<nombre-de-la-base>
DATABASE_URL=postgresql+asyncpg://<usuario>:<contraseña>@db:5432/<nombre-de-la-base>

# JWT (generar con: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=<clave-aleatoria-de-al-menos-32-caracteres>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Redis (lista de revocación de tokens al cerrar sesión)
REDIS_URL=redis://redis:6379/0    # local con Docker Compose; en Railway, la URL de su servicio de Redis

# Proveedor del modelo de lenguaje (único valor admitido: openai)
LLM_PROVIDER=openai
OPENAI_API_KEY=<clave-de-api-de-openai>
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0              # opcional; 0 = respuestas lo más reproducibles posible
OPENAI_SEED=20261003              # opcional; semilla fija de la generación

# General
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
SQL_ECHO=false                    # true: registra cada consulta SQL con sus parámetros (solo depuración local)
```

`DATABASE_URL`, `JWT_SECRET_KEY` y `REDIS_URL` son obligatorias para arrancar el backend. En `docker-compose.yml`, `REDIS_URL`, `LLM_PROVIDER`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE`, `OPENAI_SEED`, `LOG_LEVEL` y `SQL_ECHO` (`false`) tienen valores por defecto si no se definen. Cambiar el modelo, la temperatura o la semilla hace que los análisis siguientes no reutilicen resultados anteriores (sección 7). En el frontend, `VITE_API_URL` indica la URL del backend.

---

## 18. Flujos Principales

### Flujo: Registrar usuario y analizar una política

```
1. Usuario abre http://localhost:5173
2. Navega a /registro
3. Ingresa nombre, email y contraseña; marca la aceptación del aviso y la declaración de edad
4. POST /api/auth/register → JWT (se guardan privacy_accepted_at y age_declaration_at)
5. JWT se almacena en localStorage → /dashboard
6. Usuario navega a /analizar
7. Pega el texto, ingresa una URL o carga un archivo PDF/TXT
8. POST /api/ingesta/{texto|url|archivo} → texto limpio validado (RN-01)
9. Vista previa: el usuario confirma (o corrige)
10. POST /api/analisis/iniciar → 202 {id_analisis}
11. /resultados/:id consulta GET /api/analisis/{id}/estado cada 1.5 s
    11a. Segmentación de la política completa
    11b. Hasta 4 secciones en paralelo: RAG (5 + 2 guatemaltecos), llamada al modelo,
         citas construidas por el servidor, segunda pasada de respaldo
    11c. Resumen (solo hallazgos respaldados de secciones analizadas) y recomendaciones prácticas
    11d. Persistencia en analysis_temp (estado completado)
12. GET /api/analisis/{id} → semáforo, secciones, citas, filtros y recomendaciones
13. (Opcional) GET /api/analisis/{id}/pdf → reporte PDF (se registra su tiempo)
```

### Flujo: Análisis interno (analisis_service.py)

```
texto_politica
    ↓
segmentar_politica()  [encabezados + bloques de 500 palabras, sin tope de secciones]
    ↓ ["Sección 1...", "Sección 2...", ...]
    ↓
Para cada sección (hasta 4 a la vez):
    recuperar_contexto(db, sec, k=5, k_guatemala=2)
        → embedding(sec) → coseno exacto contra fragmentos activos
    _construir_contexto_normativo(chunks)
        → "[Fragmento 1]\nDocumento: ...\nJurisdicción: ...\nContenido: ..."
    llm.generar_analisis(SYSTEM_PROMPT, prompt_seccion, "")
        → JSON con hallazgos y números de fragmento
    _parsear_seccion(json_str, chunks)
        → citas con el texto real; sin fragmentos válidos → sin_respaldo
        → respuesta inválida: reintento con el motivo; segunda falla: sección de respaldo (analizada = false)
    _respaldar_hallazgos()
        → búsqueda con la descripción de cada hallazgo pendiente + SYSTEM_PROMPT_RESPALDO
    ↓
_calcular_resumen(secciones)
    → ResumenGeneral(nivel, puntaje, comentario)
_generar_recomendaciones_practicas(llm, secciones)
    → SYSTEM_PROMPT_RECOMENDACIONES (o recomendaciones básicas)
    ↓
AnalisisResponse → persistida en JSONB → consultada por el cliente
```

### Flujo: Administración

```
1. El responsable ejecuta scripts/promover_admin.py <correo>
2. La persona vuelve a iniciar sesión → el menú "Administración" aparece
3. /admin/usuarios → GET /api/admin/usuarios?q=... → activar/desactivar
   (desactivar invalida todas las sesiones de esa cuenta)
4. /admin/corpus → GET /api/admin/corpus → activar/desactivar documentos
   o cargar uno nuevo (POST /api/admin/corpus, PDF/TXT ≤ 5 MB, jurisdicción, 5/min)
```

---

*Manual técnico del Proyecto de Graduación — UMG Campus Jutiapa — actualizado en septiembre de 2026*
