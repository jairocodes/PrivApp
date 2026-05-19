"""Punto de entrada principal de la aplicación FastAPI."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.core.limiter import limiter

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Análisis de Políticas de Privacidad",
    description=(
        "API para el análisis automatizado de políticas de privacidad "
        "dirigido a jóvenes de San José Acatempa, Jutiapa. "
        "Proyecto de Graduación I — UMG Campus Jutiapa."
    ),
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.v1 import analisis, auth, ingesta  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(ingesta.router, prefix="/api/ingesta", tags=["Ingesta"])
app.include_router(analisis.router, prefix="/api/analisis", tags=["Análisis"])


@app.get("/health", tags=["Sistema"])
async def healthcheck():
    """Verifica que el servicio backend está en línea."""
    return {
        "status": "ok",
        "service": "privapp-backend",
        "version": "0.4.0",
        "environment": settings.environment,
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Backend iniciado. Entorno: %s", settings.environment)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend detenido.")
