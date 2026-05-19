# Guía de Instalación — PrivApp

## Requisitos previos

- **Docker Desktop** v4.0 o superior (incluye Docker Compose v2)
- **API key de Google Gemini** (gratuita en aistudio.google.com)
- Los PDFs del corpus normativo (ver `corpus_normativo/README.md`)
- Conexión a Internet (para descargar imágenes Docker la primera vez)

## Pasos de instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd sistema-privacidad-sja
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Abre `.env` y completa los valores:

| Variable | Descripción |
|---|---|
| `POSTGRES_PASSWORD` | Contraseña segura para PostgreSQL |
| `JWT_SECRET_KEY` | Clave secreta aleatoria (mínimo 32 caracteres) |
| `GEMINI_API_KEY` | Tu API key de Google Gemini |

Para generar una clave JWT segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Colocar los PDFs del corpus normativo

Coloca los PDFs en las carpetas indicadas en `corpus_normativo/README.md`.

### 4. Levantar el sistema

```bash
docker compose up --build
```

La primera vez tomará varios minutos (descarga de imágenes, instalación de dependencias, descarga del modelo de embeddings).

### 5. Ejecutar migraciones

En una segunda terminal:

```bash
docker compose exec backend alembic upgrade head
```

### 6. Cargar el corpus normativo

```bash
docker compose exec backend python scripts/cargar_corpus.py
```

### 7. Verificar el sistema

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

## Solución de problemas comunes

### El backend no conecta a la base de datos
Asegúrate de que el healthcheck de PostgreSQL pase antes de que el backend inicie.
Verifica con `docker compose logs db`.

### Error "GEMINI_API_KEY no configurada"
Verifica que el archivo `.env` existe y contiene la variable `GEMINI_API_KEY` con un valor real.

### Puerto 5432 ya en uso
Si tienes PostgreSQL instalado localmente, cambia el mapeo de puerto en `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # usar puerto 5433 en el host
```

### El modelo de embeddings no descarga
El modelo `paraphrase-multilingual-mpnet-base-v2` (~450 MB) se descarga automáticamente
la primera vez que se ejecuta el script de carga. Asegúrate de tener conexión a Internet.
