# PrivApp — Sistema de Análisis de Políticas de Privacidad

> Proyecto de Graduación I — Universidad Mariano Gálvez de Guatemala, Campus Jutiapa  
> **Autor:** Jairo Ardani Castillo Girón | **Carné:** 0905-22-12005  
> **Asesora:** Sheyla Esquivel | **Año:** 2026

---

## Descripción

PrivApp es un sistema web que analiza automáticamente políticas de privacidad de servicios digitales y traduce sus implicaciones a lenguaje accesible para jóvenes del municipio de San José Acatempa, Jutiapa. Utiliza arquitectura RAG (Retrieval-Augmented Generation) con corpus normativo verificable y el modelo Gemini de Google para generar análisis fundamentados en fuentes legales reales.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy async, Alembic |
| Base de datos | PostgreSQL 16 + pgvector |
| LLM | Google Gemini (gemini-1.5-flash) |
| Embeddings | Sentence Transformers (paraphrase-multilingual-mpnet-base-v2) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Infraestructura | Docker, Docker Compose |

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (incluye Docker Compose)
- API key de Google Gemini ([obtener aquí](https://aistudio.google.com/))
- Los PDFs del corpus normativo (ver `corpus_normativo/README.md`)

## Instalación rápida

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd sistema-privacidad-sja

# 2. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus valores reales (ver sección Configuración)

# 3. Coloca los PDFs del corpus normativo (ver corpus_normativo/README.md)

# 4. Levantar el sistema completo
docker compose up --build
```

El sistema estará disponible en:
- **Frontend:** http://localhost:5173
- **Backend (API + docs):** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432

## Configuración del archivo `.env`

Copia `.env.example` como `.env` y completa los valores:

```env
POSTGRES_PASSWORD=una_contrasena_segura
JWT_SECRET_KEY=clave_aleatoria_minimo_32_caracteres
GEMINI_API_KEY=tu_api_key_de_gemini
```

> **Importante:** El archivo `.env` está en `.gitignore` y nunca debe subirse al repositorio.

## Comandos principales

```bash
# Levantar el sistema
docker compose up --build

# Levantar en segundo plano
docker compose up -d --build

# Detener
docker compose down

# Cargar el corpus normativo (primera vez o tras actualización)
docker compose exec backend python scripts/cargar_corpus.py

# Ejecutar migraciones de base de datos
docker compose exec backend alembic upgrade head

# Ejecutar tests del backend
docker compose exec backend pytest

# Ver logs del backend
docker compose logs -f backend
```

## Estructura del proyecto

```
├── backend/          # API FastAPI + servicios
├── frontend/         # App React + TypeScript
├── postgres/         # Scripts de inicialización de BD
├── corpus_normativo/ # Documentos legales y estándares
└── docs/             # Documentación detallada
```

Ver [`docs/instalacion.md`](docs/instalacion.md) para instrucciones detalladas.  
Ver [`docs/arquitectura.md`](docs/arquitectura.md) para descripción técnica completa.

## Estado del prototipo (Sprint 0)

| Módulo | Estado |
|---|---|
| Infraestructura Docker | Completado |
| Autenticación (JWT) | Sprint 1 |
| Ingesta de políticas | Sprint 3 |
| Motor de Análisis (RAG + Gemini) | Sprint 4 |
| Panel de Visualización | Sprint 5 |

## Módulos excluidos del prototipo

Los siguientes módulos serán implementados en Proyecto de Graduación II:
- Repositorio histórico de análisis
- Generación de reportes descargables

## Licencia

MIT — ver [LICENSE](LICENSE)
