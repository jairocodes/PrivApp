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
import hashlib
import logging
import sys
import time
from pathlib import Path

# Necesario para que Python encuentre el paquete `app` desde scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.corpus import CorpusChunk
from app.utils.chunking import chunk_texto
from app.utils.embeddings import encode_batch
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

CATEGORIA_KEYWORDS: list[tuple[list[str], str]] = [
    (["constitucion", "constitution", "derechos_fundamentales"], "derechos_fundamentales"),
    (["rgpd", "gdpr", "lopdp", "proteccion_datos", "datos_personales"], "proteccion_datos"),
    (["laip", "acceso_informacion", "transparencia"], "acceso_informacion"),
    (["opp", "taxonomia", "ontologia"], "taxonomia_privacidad"),
    (["tosdr", "terminos_servicio", "tos"], "terminos_servicio"),
    (["oea", "parlatino", "principios"], "principios_internacionales"),
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funciones de inferencia de metadatos
# ---------------------------------------------------------------------------

def inferir_jurisdiccion(ruta: Path) -> str:
    partes = {p.lower() for p in ruta.parts}
    for clave, valor in JURISDICCION_MAP.items():
        if clave in partes:
            return valor
    return "desconocido"


def inferir_categoria(nombre: str) -> str:
    nombre_lower = nombre.lower().replace(" ", "_").replace("-", "_")
    for palabras_clave, categoria in CATEGORIA_KEYWORDS:
        if any(kw in nombre_lower for kw in palabras_clave):
            return categoria
    return "general"


def hash_chunk(documento: str, texto: str) -> str:
    contenido = f"{documento}::{texto}"
    return hashlib.md5(contenido.encode("utf-8")).hexdigest()


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
    if not texto or len(texto.split()) < 50:
        logger.warning("Texto insuficiente o vacío en '%s'. Saltando.", archivo.name)
        stats["saltados"] += 1
        return

    chunks = chunk_texto(texto)
    if not chunks:
        logger.warning("Sin chunks en '%s'. Saltando.", archivo.name)
        stats["saltados"] += 1
        return

    jurisdiccion = inferir_jurisdiccion(archivo)
    categoria = inferir_categoria(archivo.stem)
    referencia = archivo.stem.replace("_", " ").replace("-", " ").title()

    # Verificar qué hashes ya existen (deduplicación eficiente)
    hashes_nuevos = {hash_chunk(archivo.name, c): c for c in chunks}

    existentes = set()
    if hashes_nuevos:
        # Consulta de hashes existentes en lotes para evitar grandes cláusulas IN
        for h in list(hashes_nuevos.keys()):
            fila = await session.execute(
                select(CorpusChunk.id).where(
                    CorpusChunk.metadatos["hash"].astext == h
                )
            )
            if fila.scalar_one_or_none() is not None:
                existentes.add(h)

    chunks_nuevos = [(h, t) for h, t in hashes_nuevos.items() if h not in existentes]

    if not chunks_nuevos:
        logger.info("'%s': todos los chunks ya existen (%d dup).", archivo.name, len(hashes_nuevos))
        stats["duplicados"] += len(hashes_nuevos)
        return

    textos_nuevos = [t for _, t in chunks_nuevos]
    embeddings = encode_batch(textos_nuevos, show_progress=False)

    for (chunk_hash, chunk_text), embedding in zip(chunks_nuevos, embeddings):
        registro = CorpusChunk(
            documento_fuente=archivo.name,
            jurisdiccion=jurisdiccion,
            referencia=referencia,
            categoria_tematica=categoria,
            texto_original=chunk_text,
            embedding=embedding,
            metadatos={
                "hash": chunk_hash,
                "ruta_relativa": str(archivo.relative_to(CORPUS_DIR)),
            },
        )
        session.add(registro)

    await session.flush()

    insertados = len(chunks_nuevos)
    duplicados = len(hashes_nuevos) - insertados
    stats["chunks_insertados"] += insertados
    stats["duplicados"] += duplicados
    logger.info(
        "'%s': %d chunks insertados, %d duplicados. [jur=%s, cat=%s]",
        archivo.name, insertados, duplicados, jurisdiccion, categoria,
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

        extensiones_soportadas = {".pdf", ".md", ".txt"}
        archivos = sorted(
            f for f in CORPUS_DIR.rglob("*")
            if f.is_file() and f.suffix.lower() in extensiones_soportadas
        )

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
