# Changelog

Todos los cambios notables de este proyecto están documentados en este archivo.  
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).

---

## [Unreleased]

## [0.1.0] — 2026-05-18 — Sprint 0: Configuración inicial

### Added
- Estructura completa del repositorio según arquitectura definida en el prompt maestro.
- `docker-compose.yml` con servicios: PostgreSQL 16 + pgvector, backend FastAPI, frontend React.
- `Dockerfile` para backend (Python 3.11 slim) y frontend (Node 20 slim).
- `postgres/init.sql`: activación de extensiones `vector` y `uuid-ossp`, creación de tabla `corpus_chunks` con índice ivfflat.
- Skeleton de FastAPI con endpoint `GET /health` funcional.
- Skeleton de React 18 + Vite + Tailwind CSS con estructura de rutas y contexto de autenticación.
- Definición completa de modelos SQLAlchemy: `User`, `CorpusChunk`, `AnalysisTemp`.
- Schemas Pydantic v2 para autenticación y análisis.
- Interfaz abstracta `LLMAdapter` (patrón Adapter) con placeholder `GeminiAdapter`.
- Placeholders de servicios y utilidades para todos los módulos (Sprints 1–5).
- `.gitignore`, `.env.example`, `LICENSE` (MIT), `README.md`, `CONTRIBUTING.md`.
- Documentación inicial en `docs/`.
- `corpus_normativo/README.md` con instrucciones para el desarrollador.

### Notes
- Criterio de aceptación del Sprint 0 cumplido: `docker compose up --build` levanta los tres servicios.
- Los módulos funcionales (Auth, Ingesta, Motor, Panel) se implementan en Sprints 1–5.
