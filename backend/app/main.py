"""Punto de entrada principal de la aplicación FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.core.limite_carga import LimiteCargaArchivoMiddleware
from app.core.limiter import limiter
from app.core.manejadores import manejar_limite_superado, manejar_validacion
from app.core.registro import configurar_registro

configurar_registro(settings.log_level)

logger = logging.getLogger(__name__)

# Versión de la entrega del Proyecto de Graduación II (ver CHANGELOG.md).
VERSION_API = "2.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend iniciado. Entorno: %s", settings.environment)
    from app.services.analisis_service import marcar_analisis_interrumpidos

    try:
        await marcar_analisis_interrumpidos()
    except Exception:
        # Sin base de datos al arrancar, el servidor igual inicia; las rutas
        # informarán el error cuando se usen.
        logger.exception("No fue posible revisar los análisis interrumpidos.")
    yield
    logger.info("Backend detenido.")


app = FastAPI(
    title="Sistema de Análisis de Políticas de Privacidad",
    description=(
        "API para el análisis automatizado de políticas de privacidad "
        "dirigido a jóvenes de San José Acatempa, Jutiapa. "
        "Proyecto de Graduación — UMG Campus Jutiapa."
    ),
    version=VERSION_API,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, manejar_limite_superado)
app.add_exception_handler(RequestValidationError, manejar_validacion)
app.add_middleware(SlowAPIMiddleware)

# Rechazo temprano de cargas grandes: el máximo del archivo más un margen
# para el encabezado del formulario multipart.
app.add_middleware(LimiteCargaArchivoMiddleware, max_bytes=6 * 1024 * 1024)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.v1 import admin, analisis, auth, ingesta  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(ingesta.router, prefix="/api/ingesta", tags=["Ingesta"])
app.include_router(analisis.router, prefix="/api/analisis", tags=["Análisis"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administración"])


@app.get("/health", tags=["Sistema"])
async def healthcheck():
    """Verifica que el servicio backend está en línea."""
    return {
        "status": "ok",
        "service": "privapp-backend",
        "version": VERSION_API,
        "environment": settings.environment,
    }
