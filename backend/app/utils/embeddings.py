"""Servicio de generación de embeddings con Sentence Transformers.

Modelo: paraphrase-multilingual-mpnet-base-v2
Dimensión: 768
Inicialización lazy — el modelo se carga una única vez en memoria.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
CACHE_DIR = Path(__file__).parent.parent.parent / ".model_cache"
_model = None


def ruta_modelo_local(cache_dir: Path = CACHE_DIR) -> Path | None:
    """Carpeta del modelo ya descargado en la caché, o None si aún no está.

    Cargar el modelo por su nombre hace que la librería consulte en línea a
    Hugging Face aunque los archivos ya estén descargados; si esa consulta
    falla, la carga falla. Desde la carpeta local no hay ninguna consulta.
    """
    snapshots = cache_dir / f"models--sentence-transformers--{MODEL_NAME}" / "snapshots"
    completos = sorted(m.parent for m in snapshots.glob("*/modules.json"))
    return completos[-1] if completos else None


def get_model():
    """Devuelve el modelo, cargándolo la primera vez que se solicita."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        CACHE_DIR.mkdir(exist_ok=True)
        local = ruta_modelo_local()
        logger.info("Cargando modelo de embeddings '%s'%s...", MODEL_NAME, " desde la caché" if local else "")
        if local:
            _model = SentenceTransformer(str(local))
        else:
            _model = SentenceTransformer(MODEL_NAME, cache_folder=str(CACHE_DIR))
        logger.info("Modelo cargado. Dimensión: %d.", _model.get_sentence_embedding_dimension())

    return _model


def encode(texto: str) -> list[float]:
    """Genera el embedding de un texto. Devuelve vector normalizado de 768 dimensiones."""
    vector = get_model().encode(texto, normalize_embeddings=True)
    return vector.tolist()


def encode_batch(
    textos: list[str],
    batch_size: int = 32,
    show_progress: bool = False,
) -> list[list[float]]:
    """Genera embeddings para una lista de textos en lotes."""
    if not textos:
        return []
    embeddings = get_model().encode(
        textos,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
    )
    return [e.tolist() for e in embeddings]
