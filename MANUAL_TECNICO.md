# Manual Técnico — PrivApp
## Sistema de Análisis Automatizado de Políticas de Privacidad

**Proyecto de Graduación I — Universidad Mariano Gálvez, Campus Jutiapa**
**Autor:** Jairo Ardani Castillo Girón — Carné 0905-22-12005
**Fecha:** Mayo 2026
**Versión del sistema:** v1.0-prototipo (Sprint 7)

---

## Índice

1. [Descripción General](#1-descripción-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Estructura del Proyecto](#4-estructura-del-proyecto)
5. [Base de Datos](#5-base-de-datos)
6. [Backend — API REST](#6-backend--api-rest)
7. [Motor de Análisis con IA](#7-motor-de-análisis-con-ia)
8. [Arquitectura RAG](#8-arquitectura-rag)
9. [Adaptadores LLM](#9-adaptadores-llm)
10. [Frontend — Interfaz de Usuario](#10-frontend--interfaz-de-usuario)
11. [Seguridad](#11-seguridad)
12. [Configuración y Despliegue](#12-configuración-y-despliegue)
13. [Pruebas Automatizadas](#13-pruebas-automatizadas)
14. [Historial de Sprints](#14-historial-de-sprints)
15. [Variables de Entorno](#15-variables-de-entorno)
16. [Flujos Principales](#16-flujos-principales)

---

## 1. Descripción General

**PrivApp** es un sistema web que analiza automáticamente políticas de privacidad de plataformas digitales y genera reportes comprensibles para jóvenes ciudadanos de Guatemala. El sistema combina Inteligencia Artificial generativa (OpenAI GPT-4o-mini) con recuperación vectorial de normativa (RAG) para identificar riesgos de privacidad, clasificarlos por nivel de severidad y presentarlos en lenguaje accesible.

### Problema que resuelve

Los jóvenes de San José Acatempa, Jutiapa (y Guatemala en general) aceptan políticas de privacidad sin leerlas ni comprenderlas, exponiéndose a prácticas abusivas de tratamiento de datos como:
- Recopilación de datos biométricos sin finalidad declarada
- Transferencia a terceros no identificados
- Almacenamiento indefinido e irrenunciable
- Ausencia de mecanismos para eliminar datos personales

### Solución implementada

El sistema permite al usuario pegar o ingresar la URL de una política de privacidad y recibe:
- Un nivel de riesgo global (bajo / medio / alto) con puntaje 0–100
- Un desglose por secciones con hallazgos específicos
- Las referencias normativas que respaldan cada hallazgo
- Recomendaciones concretas en lenguaje accesible

---

## 2. Arquitectura del Sistema

El sistema sigue una arquitectura de **tres capas desacopladas** desplegadas mediante Docker Compose:

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUARIO (navegador)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (puerto 5173)
┌────────────────────────────▼────────────────────────────────────┐
│                    FRONTEND (React + Vite)                        │
│   Interfaz SPA con autenticación JWT y visualización de          │
│   resultados en tiempo real                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (puerto 8000)
┌────────────────────────────▼────────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                      │
│                                                                   │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────────┐  │
│  │   Auth API   │  │  Ingesta API   │  │   Análisis API      │  │
│  └──────────────┘  └────────────────┘  └──────────┬──────────┘  │
│                                                    │             │
│  ┌─────────────────────────────────────────────────▼──────────┐  │
│  │               Motor de Análisis                             │  │
│  │  Segmentación → RAG → LLM Adapter → Parseo → Resumen       │  │
│  └───────────┬───────────────────────────────┬───────────────┘  │
│              │ SQLAlchemy Async               │ OpenAI API       │
│  ┌───────────▼───────────┐       ┌───────────▼───────────────┐  │
│  │   PostgreSQL + pgvec  │       │   GPT-4o-mini (OpenAI)    │  │
│  │   (corpus + usuarios) │       │   (análisis LLM)           │  │
│  └───────────────────────┘       └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes principales

| Componente | Responsabilidad |
|---|---|
| **Frontend** | SPA React que maneja autenticación, ingesta de texto/URL y visualización de resultados |
| **Backend API** | FastAPI que expone los endpoints REST, valida requests y orquesta la lógica de negocio |
| **Motor de Análisis** | Orquestador que segmenta políticas, ejecuta RAG y llama al LLM |
| **RAG Service** | Recupera fragmentos normativos relevantes usando búsqueda vectorial coseno |
| **LLM Adapter** | Abstracción sobre OpenAI/Gemini con reintentos exponenciales |
| **PostgreSQL + pgvector** | Almacena usuarios, análisis y el corpus normativo con embeddings 768D |

---

## 3. Stack Tecnológico

### Backend

| Tecnología | Versión | Rol |
|---|---|---|
| Python | 3.11 | Lenguaje del backend |
| FastAPI | 0.115.5 | Framework API REST asíncrono |
| Uvicorn | 0.32.1 | Servidor ASGI con hot-reload |
| SQLAlchemy | 2.0.36 | ORM asíncrono (AsyncSession) |
| Alembic | 1.14.0 | Migraciones de base de datos |
| asyncpg | 0.30.0 | Driver PostgreSQL async |
| pgvector | 0.3.6 | Extensión vectorial para Python |
| Pydantic v2 | 2.10.3 | Validación de datos y schemas |
| OpenAI SDK | 1.82.0 | Cliente API GPT-4o-mini |
| Sentence Transformers | 3.3.1 | Generación de embeddings 768D |
| python-jose | 3.3.0 | JWT (HS256) |
| passlib + bcrypt | 1.7.4 / 3.2.2 | Hashing de contraseñas |
| tenacity | 9.0.0 | Reintentos con backoff exponencial |
| slowapi | 0.1.9 | Rate limiting por endpoint |
| pdfplumber | 0.11.4 | Extracción de texto desde PDF |
| BeautifulSoup4 | 4.12.3 | Extracción de texto desde HTML/URL |
| pytest + pytest-asyncio | 8.3.4 / 0.24.0 | Suite de pruebas |

### Frontend

| Tecnología | Versión | Rol |
|---|---|---|
| React | 18 | Librería UI |
| TypeScript | — | Tipado estático |
| Vite | — | Bundler con HMR |
| Tailwind CSS | — | Estilos utility-first |
| Axios | — | Cliente HTTP |

### Infraestructura

| Tecnología | Rol |
|---|---|
| Docker + Docker Compose | Contenedorización de los 3 servicios |
| PostgreSQL 16 + pgvector | Base de datos con extensión vectorial |
| pgvector/pgvector:pg16 | Imagen Docker oficial con pgvector |

---

## 4. Estructura del Proyecto

```
Proyecto/
├── .env                          ← Variables de entorno (NO en git)
├── .gitignore
├── docker-compose.yml            ← Definición de los 3 servicios
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml            ← Configuración pytest
│   │
│   ├── app/
│   │   ├── main.py               ← Punto de entrada FastAPI + routers
│   │   ├── config.py             ← Settings via pydantic-settings
│   │   ├── database.py           ← Engine async + get_db dependency
│   │   │
│   │   ├── api/
│   │   │   ├── deps.py           ← get_current_user (JWT → User)
│   │   │   └── v1/
│   │   │       ├── auth.py       ← /api/auth/*
│   │   │       ├── ingesta.py    ← /api/ingesta/*
│   │   │       └── analisis.py   ← /api/analisis/*
│   │   │
│   │   ├── core/
│   │   │   ├── security.py       ← create_access_token, hash_password, verify_password
│   │   │   ├── exceptions.py     ← HTTPException personalizadas
│   │   │   └── limiter.py        ← Instancia global SlowAPI
│   │   │
│   │   ├── models/
│   │   │   ├── user.py           ← ORM: tabla users
│   │   │   ├── analysis.py       ← ORM: tabla analysis_temp (JSONB/TEXT)
│   │   │   └── corpus.py         ← ORM: tabla corpus_chunks (vector 768D)
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py           ← RegisterRequest, LoginRequest, TokenResponse
│   │   │   ├── analysis.py       ← AnalisisResponse, SeccionAnalizada, Hallazgo...
│   │   │   ├── analisis_request.py  ← IniciarAnalisisRequest (min 100 chars)
│   │   │   └── ingesta.py        ← IngestaResponse
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py   ← register_user, authenticate_user
│   │   │   ├── ingesta_service.py← procesar_texto_directo, extraer_texto_url
│   │   │   ├── analisis_service.py ← MOTOR PRINCIPAL (ver sección 7)
│   │   │   ├── rag_service.py    ← recuperar_contexto (búsqueda vectorial)
│   │   │   └── llm/
│   │   │       ├── base.py       ← LLMAdapter ABC
│   │   │       ├── openai_adapter.py ← GPT-4o-mini (activo)
│   │   │       └── gemini_adapter.py ← Gemini 2.0 Flash (inactivo)
│   │   │
│   │   └── utils/
│   │       ├── embeddings.py     ← EmbeddingModel (paraphrase-multilingual-mpnet)
│   │       ├── chunking.py       ← Chunking + metadatos del corpus
│   │       └── pdf_extractor.py  ← Extracción texto desde PDF
│   │
│   ├── migrations/
│   │   └── versions/
│   │       ├── 0001_create_users_table.py
│   │       ├── 0002_corpus_chunks_table.py
│   │       └── 0003_analysis_temp_table.py
│   │
│   ├── tests/
│   │   ├── conftest.py           ← Fixtures: SQLite in-memory + seed_user
│   │   ├── test_auth.py          ← 18 tests autenticación
│   │   ├── test_ingesta.py       ← 16 tests ingesta
│   │   ├── test_analisis.py      ← 20 tests motor análisis
│   │   └── test_rag.py           ← 29 tests RAG, chunking, embeddings
│   │
│   └── scripts/
│       └── cargar_corpus.py      ← Carga PDFs al corpus vectorial
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx / App.tsx
│   │   ├── api/                  ← Clientes HTTP (auth, ingesta, análisis)
│   │   ├── components/
│   │   │   ├── common/           ← Navbar, Button, Input, ProtectedRoute
│   │   │   ├── auth/             ← LoginForm, RegisterForm
│   │   │   ├── ingesta/          ← IngestaForm (texto/URL, 200k chars)
│   │   │   └── analisis/         ← Semáforo, TarjetaSeccion, CitaNormativa
│   │   ├── pages/                ← Login, Register, Dashboard, Ingesta, Resultados
│   │   ├── context/              ← AuthContext (JWT en localStorage)
│   │   ├── hooks/                ← useAuth, useAnalisis
│   │   └── utils/validators.ts   ← Validaciones frontend
│   └── package.json / vite.config.ts / tailwind.config.js
│
├── postgres/
│   └── init.sql                  ← Crea extensión vector + tabla corpus_chunks
│
└── corpus_normativo/             ← PDFs fuente del corpus RAG
    ├── guatemala/
    ├── internacional/
    └── estandares_tecnicos/
```

---

## 5. Base de Datos

### Motor

**PostgreSQL 16** con extensión **pgvector** (`pgvector/pgvector:pg16`). Se usa AsyncSession de SQLAlchemy para todas las operaciones.

### Tablas

#### `users` (Alembic migración 0001)
```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    UNIQUE NOT NULL,
    hashed_password VARCHAR(255)    NOT NULL,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);
```

#### `corpus_chunks` (postgres/init.sql)
```sql
CREATE TABLE corpus_chunks (
    id                  SERIAL PRIMARY KEY,
    documento_fuente    VARCHAR(255) NOT NULL,
    jurisdiccion        VARCHAR(50)  NOT NULL,  -- 'guatemala', 'internacional', etc.
    referencia          VARCHAR(255),
    categoria_tematica  VARCHAR(100),
    texto_original      TEXT         NOT NULL,
    embedding           vector(768)  NOT NULL,  -- paraphrase-multilingual-mpnet
    metadatos           JSONB,
    fecha_carga         TIMESTAMP    DEFAULT NOW()
);

-- Índice ANN para búsqueda vectorial coseno (IVFFlat, 100 listas)
CREATE INDEX idx_corpus_embedding ON corpus_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### `analysis_temp` (Alembic migración 0003)
```sql
CREATE TABLE analysis_temp (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER  REFERENCES users(id) NOT NULL,
    texto_original  TEXT     NOT NULL,   -- primeros 2000 chars de la política
    resultado       JSONB,               -- AnalisisResponse serializado
    estado          VARCHAR(20) DEFAULT 'pendiente', -- procesando | completado
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

> **Nota técnica:** El campo `resultado` usa `JSONB` en PostgreSQL y un `TypeDecorator` personalizado (`JSONBCompat`) que lo mapea a `TEXT` cuando el motor es SQLite (para pruebas unitarias).

### Migraciones Alembic

```bash
# Crear nueva migración
docker compose exec backend alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones pendientes
docker compose exec backend alembic upgrade head

# Ver estado actual
docker compose exec backend alembic current
```

---

## 6. Backend — API REST

### Autenticación — `/api/auth`

| Método | Endpoint | Descripción | Rate Limit |
|---|---|---|---|
| `POST` | `/register` | Registro de nuevo usuario | 10/min |
| `POST` | `/login` | Autenticación → JWT 24h | 5/min |
| `POST` | `/logout` | Cierre de sesión (invalidación cliente) | — |
| `GET` | `/me` | Perfil del usuario autenticado | — |

**Validaciones de registro:**
- Contraseña: mínimo 8 caracteres, al menos una mayúscula y un número
- Email: formato válido con `email-validator`
- Nombre: mínimo 2 caracteres

### Ingesta — `/api/ingesta`

| Método | Endpoint | Descripción | Rate Limit |
|---|---|---|---|
| `POST` | `/texto` | Recibe texto pegado directamente | 20/min |
| `POST` | `/url` | Descarga y extrae texto de una URL | 10/min |

**Límites de contenido:**
- Mínimo: 200 caracteres (configurable en service)
- Máximo: 200,000 caracteres

**Proceso de limpieza (ingesta_service.py):**
1. Colapsa espacios múltiples
2. Normaliza saltos de línea excesivos
3. Normaliza Unicode (NFC)
4. Preserva saltos de párrafo

### Análisis — `/api/analisis`

| Método | Endpoint | Descripción | Rate Limit |
|---|---|---|---|
| `POST` | `/iniciar` | Inicia análisis de una política | 5/min |
| `GET` | `/{id}` | Recupera resultado de análisis completado | — |

**Request de análisis:**
```json
{
  "texto": "POLÍTICA DE PRIVACIDAD... (mín 100 chars)"
}
```

**Response de análisis:**
```json
{
  "id_analisis": "12",
  "fecha": "2026-05-20T14:30:00Z",
  "resumen_general": {
    "nivel_riesgo_global": "alto",
    "puntaje": 85,
    "comentario_breve": "Esta política presenta 5 hallazgo(s) de riesgo alto..."
  },
  "secciones_analizadas": [
    {
      "categoria_opp115": "Data Collection",
      "titulo": "Recopilación de datos biométricos",
      "texto_original": "...",
      "hallazgos": [
        {
          "tipo": "riesgo",
          "descripcion": "Se recopilan datos biométricos sin finalidad declarada",
          "nivel": "alto",
          "fuentes_normativas": [
            {
              "documento": "RGPD",
              "referencia": "Art. 9",
              "fragmento_relevante": "El tratamiento de datos biométricos..."
            }
          ]
        }
      ]
    }
  ],
  "recomendaciones": ["En 'Recopilación': Solicita al responsable..."]
}
```

### Excepciones HTTP personalizadas

| Excepción | HTTP Code | Descripción |
|---|---|---|
| `CredencialesInvalidasError` | 401 | Login fallido |
| `TokenInvalidoError` | 401 | JWT expirado/inválido |
| `UsuarioNoEncontradoError` | 404 | Usuario no existe en DB |
| `UsuarioYaExisteError` | 409 | Email duplicado en registro |
| `TextoDemasiadoCortoError` | 422 | Texto < 200 caracteres |
| `TextoDemasiadoLargoError` | 422 | Texto > 200,000 caracteres |
| `ExtraccionURLError` | 422 | URL no accesible o sin texto |
| `LLMError` | 502 | Fallo en comunicación con OpenAI |
| `AnalisisNoEncontradoError` | 404 | ID de análisis no existe |

---

## 7. Motor de Análisis con IA

El motor de análisis se encuentra en `backend/app/services/analisis_service.py` y es el componente central del sistema.

### Flujo completo

```
texto (str)
    │
    ▼
segmentar_politica()
    │  Divide en secciones por encabezados (regex)
    │  Fallback: bloques de 400 palabras
    │  Máximo: 8 secciones, mínimo 30 palabras c/u
    │
    ▼ list[str] (secciones)
    │
    ├─── Para cada sección:
    │        │
    │        ▼
    │   recuperar_contexto(db, seccion, k=5)
    │        │  Embedding 768D → búsqueda coseno en pgvector
    │        │  Retorna 5 fragmentos normativos más relevantes
    │        │
    │        ▼
    │   _construir_contexto_normativo(chunks)
    │        │  Formatea los fragmentos con documento, jurisdicción, referencia
    │        │
    │        ▼
    │   _construir_prompt_seccion(seccion, contexto)
    │        │  Genera prompt de usuario con:
    │        │  - Sección a analizar
    │        │  - Fragmentos normativos RAG
    │        │  - Instrucciones explícitas de análisis
    │        │  - Esquema JSON de salida requerido
    │        │
    │        ▼
    │   llm.generar_analisis(SYSTEM_PROMPT, user_msg, "")
    │        │  OpenAI GPT-4o-mini con response_format=json_object
    │        │  temperature=0.2 (respuestas consistentes)
    │        │
    │        ▼
    │   _parsear_seccion(json_str) → SeccionAnalizada
    │        │  Si falla: reintento con corrección explícita
    │        │  Si falla 2°: SeccionAnalizada fallback
    │
    ▼ list[SeccionAnalizada]
    │
    ▼
_calcular_resumen()  →  ResumenGeneral (nivel, puntaje 0-100)
_generar_recomendaciones()  →  list[str] (máx 5)
    │
    ▼
Persistir en analysis_temp (JSONB)
    │
    ▼
AnalisisResponse (retornado al cliente)
```

### System Prompt

El `SYSTEM_PROMPT` define el comportamiento del LLM:

- **Rol:** Experto en análisis de políticas de privacidad para jóvenes guatemaltecos
- **Cobertura normativa:** SIEMPRE reporta riesgos obvios, citando corpus cuando existe; usando "Principios generales" cuando no hay fragmento específico
- **Jurisdicción:** Distingue entre normativa guatemalteca e internacional (RGPD, LOPDP, OEA)
- **Lenguaje:** Accesible para jóvenes 13-30 años, sin jerga jurídica innecesaria
- **Criterios de riesgo ALTO:** Datos biométricos, audio pasivo, datos sensibles sin justificación, terceros no identificados, transferencia a países sin ley, conservación indefinida, sin mecanismo de eliminación, menores sin consentimiento parental, consentimiento implícito

### Cálculo del puntaje (0–100)

```python
_PESO_NIVEL = {"bajo": 1, "medio": 2, "alto": 3}

pesos = [_PESO_NIVEL[h.nivel] for h in todos_hallazgos]
promedio = sum(pesos) / len(pesos)
puntaje = min(100, int((promedio - 1) / 2 * 100))

# Nivel global:
# alto    → promedio >= 2.5  o  ≥2 hallazgos alto
# medio   → promedio >= 1.5  o  ≥2 hallazgos medio
# bajo    → resto
```

---

## 8. Arquitectura RAG

**RAG (Retrieval-Augmented Generation)** es el mecanismo que permite al LLM fundamentar sus análisis en normativa real en lugar de "inventar" referencias legales.

### Corpus normativo

El corpus contiene fragmentos de documentos normativos organizados por jurisdicción:

| Jurisdicción | Documentos incluidos |
|---|---|
| `guatemala` | Constitución Política de la República (Art. 24, 31, 44), LAIP (Ley de Acceso a la Información Pública), Acuerdo Gubernativo 214-2013 |
| `internacional` | RGPD (Reglamento General de Protección de Datos UE), LOPDP Ecuador, Principios OEA 2021, LGPD Brasil |
| `estandares_tecnicos` | ISO/IEC 29100, OWASP Privacy Risks, OPP-115 Taxonomy |

### Modelo de embeddings

```
Modelo: paraphrase-multilingual-mpnet-base-v2
Proveedor: sentence-transformers (Hugging Face)
Dimensión: 768 flotantes por vector
Idiomas: 50+ idiomas incluyendo español
Normalización: L2 (cosine similarity equivale a dot product)
```

### Proceso de carga del corpus

```bash
# Ejecutar dentro del contenedor backend
docker compose exec backend python scripts/cargar_corpus.py

# El script:
# 1. Lee PDFs del directorio /app/corpus_normativo/
# 2. Divide en chunks (~500 tokens con 10% solapamiento)
# 3. Infiere metadatos (jurisdicción, categoría)
# 4. Genera embedding 768D por chunk
# 5. Inserta en corpus_chunks con el embedding
```

### Búsqueda vectorial

```sql
-- Operador <=> = distancia coseno (pgvector)
-- Un menor valor = mayor similitud semántica
SELECT id, documento_fuente, jurisdiccion, referencia,
       categoria_tematica, texto_original, metadatos
FROM   corpus_chunks
ORDER  BY embedding <=> CAST($1 AS vector)
LIMIT  5
```

---

## 9. Adaptadores LLM

El sistema implementa el **patrón Adapter** para permitir intercambiar el proveedor LLM sin modificar el motor de análisis.

### Interfaz base (`base.py`)

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

### OpenAI Adapter (activo)

```python
# Configuración
Modelo: gpt-4o-mini
Temperature: 0.2
response_format: {"type": "json_object"}  # JSON forzado

# Reintentos (tenacity)
Intentos: 3
Wait: exponencial 2s → 10s
Reintenta en: RateLimitError, APIConnectionError
No reintenta en: errores 4xx (autenticación, modelo inválido)
```

**Selección de proveedor en `.env`:**
```
LLM_PROVIDER=openai     # usa OpenAIAdapter
LLM_PROVIDER=gemini     # usa GeminiAdapter (fallback)
```

---

## 10. Frontend — Interfaz de Usuario

### Páginas

| Página | Ruta | Descripción |
|---|---|---|
| Login | `/login` | Formulario de inicio de sesión |
| Register | `/register` | Formulario de registro con validación |
| Dashboard | `/` | Panel principal post-login |
| Ingesta | `/ingesta` | Formulario para ingresar política (texto/URL) |
| Resultados | `/resultados/:id` | Visualización del análisis generado |

### Componentes de resultados

- **IndicadorSemaforo:** Muestra el nivel de riesgo (verde/amarillo/rojo) con descripción
- **TarjetaSeccion:** Despliega cada sección analizada con sus hallazgos expandibles
- **CitaNormativa:** Muestra el fragmento normativo que respalda un hallazgo
- **ListaRecomendaciones:** Lista de acciones concretas para el usuario

### Autenticación

```typescript
// AuthContext.tsx
// - JWT almacenado en localStorage
// - Auto-logout al expirar (24h)
// - Interceptor axios para incluir Bearer token en todas las requests
```

### Límites del formulario de ingesta

```typescript
// IngestaForm.tsx
const MAX_CHARS = 200_000;
const MIN_CHARS = 200;
// Contador en tiempo real
// Acepta texto pegado o URL
```

---

## 11. Seguridad

### Autenticación JWT

```
Algoritmo: HS256
Expiración: 24 horas
Secret: variable de entorno JWT_SECRET_KEY (mín 32 bytes)
Payload: { "sub": "user_id", "exp": timestamp }
```

### Contraseñas

```
Hash: bcrypt (cost factor por defecto ~12 rounds)
Librería: passlib[bcrypt] 1.7.4 + bcrypt 3.2.2
Nunca se almacena la contraseña en texto plano
```

### Rate Limiting

```
Implementación: SlowAPI (wrapper de slowapi sobre FastAPI)
Backend de conteo: en memoria (por proceso)
Límites por endpoint:
  - POST /register: 10 req/min
  - POST /login: 5 req/min
  - POST /analisis/iniciar: 5 req/min
  - POST /ingesta/texto: 20 req/min
  - POST /ingesta/url: 10 req/min
```

### CORS

```
Orígenes permitidos: configurados en CORS_ORIGINS (.env)
Desarrollo: http://localhost:5173
Producción: dominio real del frontend
```

### Consideraciones de producción

- El archivo `.env` nunca se versiona (en `.gitignore`)
- Las API keys se leen exclusivamente de variables de entorno
- Las credenciales nunca se loguean (el logger omite `api_key`)
- Los endpoints de análisis y ingesta requieren JWT válido

---

## 12. Configuración y Despliegue

### Requisitos previos

- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Docker Compose v2+
- Git

### Primer despliegue

```bash
# 1. Clonar el repositorio
git clone <url-repo>
cd Proyecto

# 2. Crear archivo de entorno
cp .env.example .env
# Editar .env con las credenciales reales

# 3. Construir e iniciar todos los servicios
docker compose up --build

# 4. (Opcional) Cargar corpus normativo en PostgreSQL
docker compose exec backend python scripts/cargar_corpus.py

# 5. Verificar que todo está en orden
docker compose exec backend pytest tests/ -v
```

### Servicios disponibles tras el despliegue

| Servicio | URL | Descripción |
|---|---|---|
| Frontend | http://localhost:5173 | Aplicación web |
| Backend API | http://localhost:8000 | REST API |
| Documentación API | http://localhost:8000/docs | Swagger UI automático |
| Health check | http://localhost:8000/health | Estado del servicio |
| PostgreSQL | localhost:5432 | Base de datos |

### Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f backend

# Reiniciar solo el backend (aplica cambios de código)
docker compose restart backend

# Reconstruir backend (cambios en requirements.txt o Dockerfile)
docker compose build backend && docker compose up backend -d

# Ejecutar migraciones
docker compose exec backend alembic upgrade head

# Ejecutar pruebas
docker compose exec backend pytest tests/ -v

# Ejecutar pruebas con cobertura
docker compose exec backend pytest tests/ --cov=app --cov-report=term-missing

# Acceder a PostgreSQL
docker compose exec db psql -U privapp -d privapp_db

# Ver chunks cargados en corpus
docker compose exec db psql -U privapp -d privapp_db -c "SELECT COUNT(*) FROM corpus_chunks;"
```

### Reconstrucción completa (elimina datos)

```bash
docker compose down -v          # elimina contenedores y volúmenes
docker compose up --build       # reconstruye desde cero
```

---

## 13. Pruebas Automatizadas

El sistema cuenta con **83 pruebas automatizadas** que cubren todos los módulos principales.

### Resultados

```
======================== 83 passed, 5 warnings in 20.17s =======================
```

### Organización de pruebas

| Archivo | Clase(s) | Tests | Qué prueba |
|---|---|---|---|
| `test_auth.py` | TestHealthcheck, TestRegistro, TestLogin, TestRutasProtegidas | 18 | Registro, login, JWT, rutas protegidas |
| `test_ingesta.py` | TestLimpiezaTexto, TestIngestaServicio, TestEndpointsIngesta | 16 | Limpieza de texto, extracción URL, endpoints ingesta |
| `test_analisis.py` | TestSegmentacion, TestParseoJSON, TestResumen, TestEndpointsAnalisis | 20 | Segmentación, parseo JSON, cálculo resumen, endpoints análisis |
| `test_rag.py` | TestChunking, TestMetadatosCorpus, TestPdfExtractor, TestEmbeddings, TestRAGService | 29 | Chunking, metadatos, PDF, embeddings, recuperación vectorial |

### Infraestructura de pruebas

```python
# conftest.py — fixtures clave:

# SQLite in-memory (evita dependencia de PostgreSQL real)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# seed_user: crea usuario con id=1 para tests autenticados
@pytest.fixture
async def seed_user(db_session) -> User:
    user = User(nombre="Test User", email="test@privapp.test",
                hashed_password=hash_password("TestPass123"), is_active=True)
    db_session.add(user)
    await db_session.flush()
    return user

# client: AsyncClient con DB override y seed_user incluido
@pytest.fixture
async def client(db_session, seed_user) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), ...) as ac:
        yield ac
```

### Compatibilidad JSONB / SQLite

El campo `resultado` en `AnalysisTemp` usa un `TypeDecorator` personalizado:
- En **PostgreSQL**: usa `JSONB` nativo
- En **SQLite** (tests): serializa/deserializa el dict como `TEXT` + `json.dumps/loads`

---

## 14. Historial de Sprints

| Sprint | Commit | Descripción |
|---|---|---|
| Sprint 1 | `d1e74f7` | Módulo de autenticación completo (registro, login, JWT, rutas protegidas) |
| Sprint 2 | `8f8fd82` | Corpus normativo y arquitectura RAG (chunking, embeddings, pgvector) |
| Sprint 3 | `91f6043` | Ingesta de políticas (texto directo, extracción URL, Gemini Adapter) |
| Sprint 4 | `06d3a40` | Motor de análisis (RAG + LLM + endpoints + visualización básica) |
| Sprint 5 | `48a569e` | Panel de visualización mobile-first (semáforo, secciones, citas normativas) |
| Sprint 6 | `dc5468e` | Documentación final del prototipo v1.0 |
| v1.0 | `e98e50a` | Release oficial del prototipo |
| Sprint 7 | `27cccac` | Migración a OpenAI, límite 200k chars, pruebas corregidas (83/83 ✓) |

---

## 15. Variables de Entorno

Archivo `.env` (nunca versionar):

```bash
# Base de datos
POSTGRES_USER=privapp
POSTGRES_PASSWORD=<contraseña-segura>
POSTGRES_DB=privapp_db
DATABASE_URL=postgresql+asyncpg://privapp:<password>@db:5432/privapp_db

# JWT (generar con: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=<clave-aleatoria-minimo-32-bytes>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Proveedor LLM activo
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Google Gemini (inactivo, mantenido por compatibilidad)
#GEMINI_API_KEY=...
#GEMINI_MODEL=gemini-2.0-flash

# General
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
```

---

## 16. Flujos Principales

### Flujo: Registrar usuario y analizar política

```
1. Usuario abre http://localhost:5173
2. Navega a /register
3. Ingresa nombre, email, contraseña
4. POST /api/auth/register → recibe JWT
5. JWT se almacena en localStorage
6. Redirección a Dashboard
7. Usuario navega a /ingesta
8. Pega texto de política de privacidad (o ingresa URL)
9. POST /api/ingesta/texto → texto procesado y contado
10. POST /api/analisis/iniciar → análisis inicia
    10a. Segmentación en secciones
    10b. RAG: 5 fragmentos normativos por sección
    10c. OpenAI GPT-4o-mini genera análisis JSON
    10d. Cálculo de resumen y puntaje
    10e. Persistencia en analysis_temp
11. Redirección a /resultados/:id
12. Visualización de semáforo, secciones y recomendaciones
```

### Flujo: Análisis interno (analisis_service.py)

```
texto_politica
    ↓
segmentar_politica()  [regex + fallback bloques]
    ↓ ["Sección 1...", "Sección 2...", ...]
    ↓
Para cada sección:
    recuperar_contexto(db, sec, k=5)
        → embedding(sec) → coseno contra corpus_chunks
        → top-5 fragmentos normativos
    _construir_contexto_normativo(chunks)
        → "[Fragmento 1]\nDocumento: RGPD\n..."
    _construir_prompt_seccion(sec, contexto)
        → prompt completo con esquema JSON y criterios
    openai.generar_analisis(SYSTEM_PROMPT, user_msg, "")
        → JSON con hallazgos y fuentes normativas
    _parsear_seccion(json_str)
        → SeccionAnalizada(hallazgos=[...])
    ↓
_calcular_resumen(secciones)
    → ResumenGeneral(nivel="alto", puntaje=85, ...)
_generar_recomendaciones(secciones)
    → ["En 'Recopilación de datos': Solicita..."]
    ↓
AnalisisResponse → persistida en JSONB → retornada al cliente
```

---

*Manual técnico generado para la presentación del Proyecto de Graduación I — UMG Campus Jutiapa — Mayo 2026*
