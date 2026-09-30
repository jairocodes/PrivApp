# Guía de Instalación — PrivApp

## Requisitos previos

- **Docker Desktop** v4.0 o superior (incluye Docker Compose v2)
- **API key de OpenAI** con acceso al modelo `gpt-4o-mini` (platform.openai.com)
- Conexión a Internet (para descargar imágenes Docker, dependencias y el modelo de
  embeddings la primera vez, y para las llamadas a OpenAI)
- Opcional, para correr las pruebas del frontend fuera de Docker: **Node.js 20**

Docker Compose levanta cuatro servicios: `db` (PostgreSQL 16 con pgvector), `redis`
(Redis 7, lista de sesiones revocadas), `backend` (FastAPI, Python 3.11) y `frontend`
(React + Vite).

## Pasos de instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd PrivApp
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Abre `.env` y completa los valores. Nunca subas `.env` al repositorio.

| Variable | Descripción |
|---|---|
| `POSTGRES_USER` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | Contraseña segura para PostgreSQL |
| `POSTGRES_DB` | Nombre de la base de datos |
| `DATABASE_URL` | Cadena de conexión `postgresql+asyncpg://` con el usuario, la contraseña y la base anteriores; en Docker Compose el host es `db` y el puerto 5432 |
| `JWT_SECRET_KEY` | Clave secreta aleatoria (mínimo 32 caracteres) |
| `JWT_ALGORITHM` | Algoritmo de firma del token (HS256) |
| `JWT_EXPIRATION_HOURS` | Vigencia del token en horas (24 por defecto) |
| `REDIS_URL` | Conexión a Redis para la revocación de sesiones; en Docker Compose, el servicio `redis` en el puerto 6379 (base 0) |
| `LLM_PROVIDER` | Proveedor del modelo de lenguaje; el único soportado es `openai` |
| `OPENAI_API_KEY` | Tu API key de OpenAI |
| `OPENAI_MODEL` | Modelo de OpenAI (`gpt-4o-mini`) |
| `ENVIRONMENT` | `development` o `production` |
| `CORS_ORIGINS` | Orígenes permitidos para el frontend, separados por comas |
| `LOG_LEVEL` | Nivel de los registros del servidor (`INFO` por defecto) |

`.env.example` trae en `REDIS_URL` una dirección de ejemplo con usuario y contraseña
para un Redis externo. Para trabajar en local con Docker Compose, reemplázala por la del
servicio `redis` o deja la variable vacía: el backend usa entonces la del servicio.

Para generar una clave JWT segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Revisar el corpus normativo

Los documentos del corpus ya vienen en `corpus_normativo/`, en tres carpetas por
jurisdicción: `guatemala/`, `internacional/` y `estandares_tecnicos/`. El script de
carga solo toma los archivos PDF, TXT o MD que estén dentro de esas carpetas (el README
y cualquier otro archivo del directorio se ignoran). Para agregar un documento,
colócalo en la carpeta que corresponde a su jurisdicción.

### 4. Levantar el sistema

```bash
docker compose up --build
```

La primera vez tomará varios minutos (descarga de imágenes e instalación de
dependencias). En este modo el backend arranca con `--reload` para recargar el código
montado; la imagen de producción (`CMD` del `backend/Dockerfile`) no usa `--reload` y
arranca con `--proxy-headers --forwarded-allow-ips="*"` (la plataforma de despliegue no
publica IP fijas) y `--no-access-log` (para no registrar la IP de cada solicitud).

### 5. Ejecutar migraciones

En una segunda terminal:

```bash
docker compose exec backend alembic upgrade head
```

Esto aplica las migraciones 0001 a 0009 (tablas, rol y fechas de aceptación del aviso
y de declaración de edad, estado activo de los fragmentos del corpus, extensión
`unaccent` y búsqueda exacta sin índice vectorial).

La migración 0007 ejecuta `CREATE EXTENSION unaccent`: el usuario de `DATABASE_URL`
debe tener permiso para crear extensiones. Con el contenedor `db` de Docker Compose el
usuario de `POSTGRES_USER` es el dueño de la base y lo tiene; en un servicio de
PostgreSQL administrado, activa la extensión con un usuario autorizado si la migración
falla por permisos.

### 6. Cargar el corpus normativo

```bash
docker compose exec backend python scripts/cargar_corpus.py
```

El script segmenta cada documento, genera sus embeddings y los guarda en
`corpus_chunks`. La primera ejecución descarga el modelo de embeddings
`paraphrase-multilingual-mpnet-base-v2` (~450 MB). Es idempotente: cada fragmento lleva
un hash y los repetidos no se vuelven a insertar, así que puede ejecutarse de nuevo tras
agregar documentos. Con `--limpiar` vacía la tabla antes de cargar (pide confirmación).

Un administrador también puede incorporar documentos desde `/admin/corpus` (PDF o TXT
de hasta 5 MB; el nombre del archivo identifica al documento y uno repetido se rechaza).

### 7. Crear el primer administrador

Registra una cuenta desde el frontend y promuévela:

```bash
docker compose exec backend python scripts/promover_admin.py correo@ejemplo.com
```

Es la única forma de asignar el rol administrador. La persona debe cerrar sesión y
volver a iniciarla para que su token lleve el rol; el servidor la reconoce como
administradora desde el momento del cambio.

### 8. Verificar el sistema

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

## Ejecutar las pruebas

### Backend (pytest)

```bash
docker compose exec backend pytest
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

Las pruebas usan SQLite en memoria y no llaman a OpenAI. Las pruebas de integración de
`tests/integracion` se ejecutan contra PostgreSQL solo si se define
`PRIVAPP_TEST_PG_URL` con la cadena de conexión de una base con las migraciones
aplicadas; si no, se omiten:

```bash
docker compose exec -e PRIVAPP_TEST_PG_URL=<cadena-de-conexion> backend pytest tests/integracion
```

**Importante:** estas pruebas vacían las tablas. Usa una base creada solo para
pruebas; nunca apuntes `PRIVAPP_TEST_PG_URL` a una base con datos reales.

### Frontend (Vitest)

```bash
docker compose exec frontend npm test -- --run
```

O, con Node.js instalado:

```bash
cd frontend
npm install
npm test -- --run
```

Las pruebas usan jsdom. Sin `--run`, Vitest queda en modo de observación y repite las
pruebas al guardar cambios.

## Herramientas adicionales

Resumen de los tiempos de generación del reporte PDF (promedio, mediana, mínimo, máximo
y percentil 95):

```bash
docker compose exec backend python scripts/tiempos_reporte.py
docker compose exec backend python scripts/tiempos_reporte.py --detalle
```

## Solución de problemas comunes

### El backend no conecta a la base de datos
Asegúrate de que el healthcheck de PostgreSQL pase antes de que el backend inicie.
Verifica con `docker compose logs db` y revisa que el host de `DATABASE_URL` sea `db`.

### Error al iniciar sesión o en cualquier ruta autenticada
Cada solicitud autenticada consulta Redis para comprobar si la sesión fue cerrada.
Verifica que el servicio `redis` esté en línea (`docker compose logs redis`) y que
`REDIS_URL` apunte a él (ver el paso 2).

### Todas las secciones aparecen como "No fue posible analizar esta sección automáticamente"
El backend no pudo usar el modelo de OpenAI. Verifica que `.env` contenga
`OPENAI_API_KEY` con un valor real, que `LLM_PROVIDER` sea `openai` y que la cuenta de
OpenAI tenga saldo. Revisa `docker compose logs backend`.

### La migración 0007 falla con un error de permisos
El usuario de la base no puede crear la extensión `unaccent`. Actívala con un usuario
autorizado o concede el permiso y vuelve a ejecutar `alembic upgrade head` (ver el
paso 5).

### Una prueba de sesiones falla sola
En Docker Desktop con WSL2 el reloj del contenedor puede retroceder unos 32 segundos
cada 30 segundos. Las pruebas de sesiones comparan la hora de emisión del token con la
de invalidación, así que pueden fallar de forma ocasional. Repite la suite; si ocurre a
menudo, actualiza WSL con `wsl --update`.

### Puerto 5432 ya en uso
Si tienes PostgreSQL instalado localmente, cambia el mapeo de puerto en `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # usar puerto 5433 en el host
```

### El modelo de embeddings no descarga
El modelo `paraphrase-multilingual-mpnet-base-v2` (~450 MB) se descarga automáticamente
la primera vez que se ejecuta el script de carga y queda guardado en
`backend/.model_cache/`. Asegúrate de tener conexión a Internet.
