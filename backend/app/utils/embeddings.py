"""Servicio de generación de embeddings con Sentence Transformers.

Modelo: paraphrase-multilingual-mpnet-base-v2
Dimensión: 768
Inicialización lazy — el modelo se carga una única vez en memoria.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
_model = None


def get_model():
    """Devuelve el modelo, cargándolo la primera vez que se solicita."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        cache_dir = Path(__file__).parent.parent.parent / ".model_cache"
        cache_dir.mkdir(exist_ok=True)

        logger.info("Cargando modelo de embeddings '%s'...", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME, cache_folder=str(cache_dir))
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
