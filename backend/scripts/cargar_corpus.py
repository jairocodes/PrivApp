#!/usr/bin/env python3
"""Script de carga del corpus normativo en la base de datos vectorial.

Uso:
    docker compose exec backend python scripts/cargar_corpus.py
    docker compose exec backend python scripts/cargar_corpus.py --limpiar

El script es idempotente: usa un hash MD5 por chunk para evitar duplicados.
Al final imprime estadísticas de la carga.
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Necesario para que Python encuentre el paquete `app` desde scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.services.corpus_service import (  # noqa: F401 (hash_chunk e inferir_categoria se reexportan)
    MIN_PALABRAS_DOCUMENTO,
    hash_chunk,
    inferir_categoria,
    insertar_fragmentos,
)
from app.utils.pdf_extractor import extraer_texto_pdf

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus_normativo"

JURISDICCION_MAP: dict[str, str] = {
    "guatemala": "guatemala",
    "internacional": "internacional",
    "estandares_tecnicos": "estandar_tecnico",
}

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funciones de inferencia de metadatos
# ---------------------------------------------------------------------------

EXTENSIONES_SOPORTADAS = {".pdf", ".md", ".txt"}


def archivos_del_corpus(directorio: Path) -> list[Path]:
    """Archivos que forman parte del corpus: solo los que están dentro de una
    carpeta de jurisdicción (guatemala, internacional, estandares_tecnicos).
    Así se excluyen el README y cualquier otra nota o documentación del
    directorio que no sea normativa."""
    return sorted(
        f for f in directorio.rglob("*")
        if f.is_file()
        and f.suffix.lower() in EXTENSIONES_SOPORTADAS
        and f.relative_to(directorio).parts[0].lower() in JURISDICCION_MAP
    )


def inferir_jurisdiccion(ruta: Path) -> str:
    partes = {p.lower() for p in ruta.parts}
    for clave, valor in JURISDICCION_MAP.items():
        if clave in partes:
            return valor
    return "desconocido"


# ---------------------------------------------------------------------------
# Procesamiento de archivos
# ---------------------------------------------------------------------------

def extraer_texto(archivo: Path) -> str:
    ext = archivo.suffix.lower()
    if ext == ".pdf":
        return extraer_texto_pdf(archivo)
    if ext in (".md", ".txt"):
        return archivo.read_text(encoding="utf-8", errors="ignore")
    return ""


async def cargar_archivo(
    session: AsyncSession,
    archivo: Path,
    stats: dict,
) -> None:
    texto = extraer_texto(archivo)
    if not texto or len(texto.split()) < MIN_PALABRAS_DOCUMENTO:
        logger.warning("Texto insuficiente o vacío en '%s'. Saltando.", archivo.name)
        stats["saltados"] += 1
        return

    jurisdiccion = inferir_jurisdiccion(archivo)
    insertados, duplicados = await insertar_fragmentos(
        session,
        archivo.name,
        texto,
        jurisdiccion,
        {"ruta_relativa": str(archivo.relative_to(CORPUS_DIR))},
    )

    if insertados == 0 and duplicados == 0:
        logger.warning("Sin chunks en '%s'. Saltando.", archivo.name)
        stats["saltados"] += 1
        return
    if insertados == 0:
        logger.info("'%s': todos los chunks ya existen (%d dup).", archivo.name, duplicados)
        stats["duplicados"] += duplicados
        return

    stats["chunks_insertados"] += insertados
    stats["duplicados"] += duplicados
    logger.info(
        "'%s': %d chunks insertados, %d duplicados. [jur=%s, cat=%s]",
        archivo.name, insertados, duplicados, jurisdiccion, inferir_categoria(archivo.stem),
    )


# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------

async def main(limpiar: bool = False) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    if not CORPUS_DIR.exists():
        logger.error("Directorio corpus_normativo no encontrado: %s", CORPUS_DIR)
        sys.exit(1)

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    t_inicio = time.time()
    stats: dict = {
        "documentos": 0,
        "chunks_insertados": 0,
        "duplicados": 0,
        "saltados": 0,
        "errores": 0,
    }

    async with session_factory() as session:
        # Verificar que la tabla existe
        try:
            await session.execute(text("SELECT 1 FROM corpus_chunks LIMIT 1"))
        except Exception:
            logger.error(
                "La tabla corpus_chunks no existe. Ejecuta primero: alembic upgrade head"
            )
            await engine.dispose()
            sys.exit(1)

        if limpiar:
            confirmacion = input(
                "\n¿Limpiar corpus_chunks antes de cargar? Esto eliminará TODOS los datos. (s/N): "
            )
            if confirmacion.strip().lower() == "s":
                await session.execute(
                    text("TRUNCATE TABLE corpus_chunks RESTART IDENTITY")
                )
                await session.commit()
                logger.info("Tabla corpus_chunks vaciada.")
            else:
                logger.info("Limpieza cancelada.")

        archivos = archivos_del_corpus(CORPUS_DIR)

        if not archivos:
            logger.warning("No se encontraron archivos en %s.", CORPUS_DIR)
            await engine.dispose()
            return

        logger.info("Archivos a procesar: %d", len(archivos))

        for archivo in archivos:
            logger.info("── Procesando: %s", archivo.relative_to(CORPUS_DIR))
            try:
                await cargar_archivo(session, archivo, stats)
                stats["documentos"] += 1
            except Exception as exc:
                logger.error("Error procesando '%s': %s", archivo.name, exc, exc_info=True)
                stats["errores"] += 1

        await session.commit()

    await engine.dispose()

    elapsed = time.time() - t_inicio
    sep = "=" * 52
    print(f"\n{sep}")
    print("  CARGA DEL CORPUS NORMATIVO — COMPLETADA")
    print(sep)
    print(f"  Documentos procesados  : {stats['documentos']}")
    print(f"  Chunks insertados      : {stats['chunks_insertados']}")
    print(f"  Chunks duplicados      : {stats['duplicados']}")
    print(f"  Archivos saltados      : {stats['saltados']}")
    print(f"  Errores                : {stats['errores']}")
    print(f"  Tiempo total           : {elapsed:.1f}s")
    print(sep)

    if stats["errores"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Carga el corpus normativo en la base de datos vectorial."
    )
    parser.add_argument(
        "--limpiar",
        action="store_true",
        help="Vaciar corpus_chunks antes de cargar (pide confirmación).",
    )
    args = parser.parse_args()
    asyncio.run(main(limpiar=args.limpiar))
