# PrivApp — Sistema de Análisis de Políticas de Privacidad

> Proyecto de Graduación — Universidad Mariano Gálvez de Guatemala, Campus Jutiapa  
> **Autor:** Jairo Ardani Castillo Girón | **Carné:** 0905-22-12005  
> **Asesora:** Sheyla Esquivel | **Año:** 2026

---

## Descripción

PrivApp es un sistema web que analiza automáticamente políticas de privacidad de servicios digitales y traduce sus implicaciones a lenguaje accesible para jóvenes del municipio de San José Acatempa, Jutiapa. Utiliza arquitectura RAG (Retrieval-Augmented Generation) sobre un corpus normativo verificable (normativa guatemalteca, referencias internacionales y estándares técnicos) y el modelo GPT-4o-mini de OpenAI para generar análisis fundamentados en fuentes legales reales.

## Funciones principales

- **Cuentas de usuario:** registro con aceptación del aviso de privacidad y declaración de edad o de consentimiento de la madre, el padre o la persona encargada; inicio y cierre de sesión con revocación de tokens.
- **Ingesta de políticas:** texto pegado, URL de un sitio web público o archivo PDF/TXT (máximo 5 MB, procesado en memoria y descartado), con vista previa obligatoria antes de analizar.
- **Análisis completo:** la política se divide en secciones que se analizan en paralelo, con progreso visible; cada sección se contrasta con fragmentos del corpus, incluidos siempre fragmentos guatemaltecos.
- **Citas verificables:** el servidor arma cada cita con el extracto real del corpus y su jurisdicción (Guatemala, Internacional o Estándar técnico); los hallazgos sin respaldo y las secciones que no pudieron analizarse se marcan y no cuentan para el nivel ni la puntuación de riesgo.
- **Resultados claros:** semáforo, puntuación de riesgo (0–100), tipo de tratamiento de datos por hallazgo, filtros por nivel y jurisdicción, ayuda del glosario junto a los términos técnicos y recomendaciones prácticas redactadas a partir de los riesgos encontrados.
- **Reporte PDF** descargable de cada análisis.
- **Historial** con búsqueda sin distinción de acentos, filtros por nivel y fechas, y eliminación definitiva de análisis.
- **Panel estadístico** personal: total de análisis, puntuación promedio y distribución por nivel de riesgo.
- **Perfil:** edición del nombre, cambio de contraseña (cierra las demás sesiones) y eliminación de la cuenta con todos sus análisis.
- **Glosario** y **aviso de privacidad** públicos.
- **Administración:** gestión de usuarios (activar o desactivar cuentas) y del corpus normativo (cargar, activar o desactivar documentos).
- **Privacidad por diseño:** los registros del servidor no contienen datos personales, se aplican límites de solicitudes por IP y la ingesta por URL solo descarga sitios web públicos.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy async, Alembic, SlowAPI |
| Base de datos | PostgreSQL 16 + pgvector |
| Sesiones | JWT + Redis (lista de revocación) |
| LLM | OpenAI (`gpt-4o-mini`) |
| Embeddings | Sentence Transformers (`paraphrase-multilingual-mpnet-base-v2`, local) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, recharts |
| Pruebas | pytest (backend), Vitest + Testing Library (frontend) |
| Infraestructura | Docker, Docker Compose |

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) v4.0+ (incluye Docker Compose v2)
- API key de OpenAI — [obtener en platform.openai.com](https://platform.openai.com/api-keys)
- Documentos del corpus normativo (ver `corpus_normativo/README.md`)

## Arranque rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/jairocodes/PrivApp.git
cd PrivApp

# 2. Configurar variables de entorno
cp .env.example .env
# Edita .env y completa tus propios valores (ver la sección siguiente)

# 3. Colocar los documentos del corpus en corpus_normativo/guatemala/,
#    corpus_normativo/internacional/ y corpus_normativo/estandares_tecnicos/

# 4. Levantar el sistema
docker compose up --build

# 5. En otra terminal: ejecutar migraciones y cargar el corpus
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/cargar_corpus.py

# 6. (Opcional) Promover a administrador una cuenta ya registrada
docker compose exec backend python scripts/promover_admin.py correo@ejemplo.com
```

El sistema estará disponible en:
- **Frontend:** http://localhost:5173
- **API (Swagger UI):** http://localhost:8000/docs
- **Healthcheck:** http://localhost:8000/health

La persona promovida a administrador debe volver a iniciar sesión para ver la opción **Administración**.

Para instrucciones detalladas ver [`docs/instalacion.md`](docs/instalacion.md).

## Configuración del archivo `.env`

Copia `.env.example` como `.env` y reemplaza los valores de ejemplo por los tuyos:

| Variable | Descripción |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credenciales de la base de datos |
| `DATABASE_URL` | Cadena de conexión (`postgresql+asyncpg://…@db:5432/…`) |
| `JWT_SECRET_KEY` | Clave aleatoria de al menos 32 caracteres |
| `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS` | Algoritmo y vigencia del token |
| `REDIS_URL` | Redis para revocar tokens; el valor de `.env.example` (`redis://redis:6379/0`) sirve en local tal cual; en Railway, la URL de su servicio de Redis |
| `LLM_PROVIDER` | `openai` |
| `OPENAI_API_KEY` | Tu API key de OpenAI |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `OPENAI_TEMPERATURE`, `OPENAI_SEED` | Opcionales: `0` y una semilla fija por defecto, para que el mismo texto dé el mismo resultado |
| `ENVIRONMENT`, `CORS_ORIGINS`, `LOG_LEVEL` | Configuración general |
| `SQL_ECHO` | `true` registra cada consulta SQL con sus parámetros (solo para depurar en local); `false` por defecto |

> El archivo `.env` está en `.gitignore` y **nunca debe subirse al repositorio**.

Para generar una clave JWT segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Comandos principales

```bash
# Levantar el sistema (en segundo plano: agregar -d)
docker compose up --build

# Detener
docker compose down

# Ejecutar migraciones
docker compose exec backend alembic upgrade head

# Cargar / recargar corpus normativo (idempotente)
docker compose exec backend python scripts/cargar_corpus.py

# Promover un administrador
docker compose exec backend python scripts/promover_admin.py correo@ejemplo.com

# Tiempos de generación del reporte
docker compose exec backend python scripts/tiempos_reporte.py [--detalle]

# Pruebas del backend (pytest)
docker compose exec backend pytest --cov=app

# Pruebas del frontend (Vitest)
docker compose exec frontend npx vitest run

# Ver registros
docker compose logs -f backend
```

## Estructura del proyecto

```
├── backend/            # API FastAPI, servicios, migraciones, pruebas
│   ├── app/
│   │   ├── api/v1/     # Routers: auth, ingesta, analisis, admin
│   │   ├── core/       # Seguridad, límites, revocación de tokens, registros
│   │   ├── repositories/
│   │   ├── services/   # auth, ingesta, rag, analisis, reportes, corpus, admin, llm/
│   │   └── utils/      # chunking, embeddings, pdf_extractor, validación de texto
│   ├── migrations/     # Versiones Alembic (0001–0011)
│   ├── scripts/        # cargar_corpus.py, promover_admin.py, tiempos_reporte.py
│   └── tests/          # Pruebas pytest (integracion/ contra PostgreSQL)
├── frontend/           # App React + TypeScript
│   └── src/
│       ├── components/ # admin/, analisis/, auth/, common/, dashboard/, glosario/,
│       │               # historial/, ingesta/, perfil/
│       ├── pages/      # Login, Register, Dashboard, Ingesta, Resultados, Historial,
│       │               # Perfil, Glosario, AvisoPrivacidad, Admin, AdminUsuarios, AdminCorpus
│       ├── data/       # Textos del glosario, del aviso y consejos de privacidad
│       └── hooks/
├── corpus_normativo/   # Documentos de normativa guatemalteca e internacional
│   ├── guatemala/
│   ├── internacional/
│   ├── estandares_tecnicos/
│   └── originales/     # Documentos fuente que no se cargan (PDF original de los Principios OEA 2021)
├── docs/               # Documentación detallada
└── postgres/           # init.sql (pgvector, corpus_chunks igual que en las migraciones)
```

## Documentación adicional

| Documento | Descripción |
|---|---|
| [`MANUAL_TECNICO.md`](MANUAL_TECNICO.md) | Manual técnico completo del sistema |
| [`docs/instalacion.md`](docs/instalacion.md) | Instalación detallada y solución de problemas |
| [`docs/api.md`](docs/api.md) | Referencia de endpoints REST |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Decisiones de diseño técnico |
| [`docs/guia_evaluador.md`](docs/guia_evaluador.md) | Guía paso a paso para evaluadores |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Flujo de ramas, commits y pruebas |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de cambios |

## Licencia

MIT — ver [LICENSE](LICENSE)
