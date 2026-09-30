# PrivApp — Sistema de Análisis de Políticas de Privacidad

> Proyecto de Graduación I — Universidad Mariano Gálvez de Guatemala, Campus Jutiapa  
> **Autor:** Jairo Ardani Castillo Girón | **Carné:** 0905-22-12005  
> **Asesora:** Sheyla Esquivel | **Año:** 2026

---

## Descripción

PrivApp es un sistema web que analiza automáticamente políticas de privacidad de servicios digitales y traduce sus implicaciones a lenguaje accesible para jóvenes del municipio de San José Acatempa, Jutiapa. Utiliza arquitectura RAG (Retrieval-Augmented Generation) con corpus normativo verificable y el modelo GPT-4o-mini de OpenAI para generar análisis fundamentados en fuentes legales reales.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy async, Alembic |
| Base de datos | PostgreSQL 16 + pgvector |
| LLM | OpenAI (`gpt-4o-mini`) |
| Embeddings | Sentence Transformers (`paraphrase-multilingual-mpnet-base-v2`, local) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Infraestructura | Docker, Docker Compose |

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) v4.0+ (incluye Docker Compose v2)
- API key de OpenAI — [obtener en platform.openai.com](https://platform.openai.com/api-keys)
- PDFs del corpus normativo (ver `corpus_normativo/README.md`)

## Instalación rápida

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd sistema-privacidad-sja

# 2. Configurar variables de entorno
cp .env.example .env
# Edita .env y completa: POSTGRES_PASSWORD, JWT_SECRET_KEY, OPENAI_API_KEY

# 3. Colocar los PDFs del corpus normativo (ver corpus_normativo/README.md)

# 4. Levantar el sistema
docker compose up --build

# 5. En otra terminal: ejecutar migraciones y cargar corpus
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/cargar_corpus.py
```

El sistema estará disponible en:
- **Frontend:** http://localhost:5173
- **API (Swagger UI):** http://localhost:8000/docs
- **Healthcheck:** http://localhost:8000/health

Para instrucciones detalladas ver [`docs/instalacion.md`](docs/instalacion.md).

## Configuración del archivo `.env`

```env
# Base de datos
POSTGRES_USER=privapp
POSTGRES_PASSWORD=tu_contrasena_segura
POSTGRES_DB=privapp_db
DATABASE_URL=postgresql+asyncpg://privapp:tu_contrasena_segura@db:5432/privapp_db

# JWT
JWT_SECRET_KEY=clave_aleatoria_minimo_32_caracteres
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI
OPENAI_API_KEY=tu_api_key_de_openai
OPENAI_MODEL=gpt-4o-mini

# General
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
```

> El archivo `.env` está en `.gitignore` y **nunca debe subirse al repositorio**.

Para generar una clave JWT segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Comandos principales

```bash
# Levantar el sistema
docker compose up --build

# Levantar en segundo plano
docker compose up -d --build

# Detener
docker compose down

# Cargar / recargar corpus normativo
docker compose exec backend python scripts/cargar_corpus.py

# Ejecutar migraciones
docker compose exec backend alembic upgrade head

# Ejecutar tests del backend
docker compose exec backend pytest --cov=app

# Ver logs
docker compose logs -f backend
```

## Estado del prototipo v1.0

| Módulo | Estado | Sprint |
|---|---|---|
| Infraestructura Docker | Completado | Sprint 0 |
| Autenticación JWT (registro, login, logout, `/me`) | Completado | Sprint 1 |
| Corpus normativo + arquitectura RAG | Completado | Sprint 2 |
| Ingesta de políticas (texto directo + URL) | Completado | Sprint 3 |
| Motor de Análisis (RAG + OpenAI + OPP-115) | Completado | Sprint 4 |
| Panel de Visualización (mobile-first) | Completado | Sprint 5 |

**Módulos excluidos del prototipo** (se implementarán en Proyecto de Graduación II):
- Repositorio histórico de análisis
- Generación de reportes descargables en PDF

## Estructura del proyecto

```
├── backend/            # API FastAPI, servicios, migraciones, tests
│   ├── app/
│   │   ├── api/v1/     # Routers: auth, ingesta, analisis
│   │   ├── services/   # auth, ingesta, rag, analisis, llm/
│   │   └── utils/      # chunking, embeddings, pdf_extractor
│   ├── migrations/     # Versiones Alembic (0001–0003)
│   ├── scripts/        # cargar_corpus.py
│   └── tests/          # 65+ tests pytest
├── frontend/           # App React + TypeScript
│   └── src/
│       ├── components/ # auth/, analisis/, ingesta/, common/
│       ├── pages/      # Login, Register, Dashboard, Ingesta, Resultados
│       └── hooks/      # useAuth, useAnalisis
├── corpus_normativo/   # PDFs de normativa guatemalteca e internacional
│   ├── guatemala/
│   ├── internacional/
│   └── estandares_tecnicos/
├── docs/               # Documentación detallada
└── postgres/           # init.sql (pgvector, corpus_chunks)
```

## Documentación adicional

| Documento | Descripción |
|---|---|
| [`docs/instalacion.md`](docs/instalacion.md) | Instalación detallada y solución de problemas |
| [`docs/api.md`](docs/api.md) | Referencia de endpoints REST |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Decisiones de diseño técnico |
| [`docs/guia_evaluador.md`](docs/guia_evaluador.md) | Guía paso a paso para evaluadores |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de cambios por Sprint |

## Licencia

MIT — ver [LICENSE](LICENSE)
