"""Chunking semántico de texto para el corpus normativo.

Parámetros del spec:
- Tamaño objetivo: 300-500 palabras por chunk
- Solapamiento: 50 palabras entre chunks consecutivos
- Estrategia: separación por párrafos primero, respetando artículos/principios numerados
"""

import re

CHUNK_SIZE_WORDS = 400
CHUNK_MAX_WORDS = 500
OVERLAP_WORDS = 50
MIN_CHUNK_WORDS = 50


def chunk_texto(
    texto: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    chunk_max: int = CHUNK_MAX_WORDS,
    overlap: int = OVERLAP_WORDS,
    min_words: int = MIN_CHUNK_WORDS,
) -> list[str]:
    """Divide el texto en chunks con solapamiento.

    Respeta límites de párrafos. Si un párrafo supera el límite máximo,
    lo divide a nivel de oración. Aplica solapamiento al inicio de cada nuevo chunk.
    """
    texto = _normalizar(texto)
    if not texto:
        return []

    parrafos = _dividir_parrafos(texto)
    if not parrafos:
        return []

    chunks: list[str] = []
    palabras_actuales: list[str] = []

    for parrafo in parrafos:
        palabras_parrafo = parrafo.split()

        # Párrafo gigante: dividirlo a nivel de oración antes de acumularlo
        if len(palabras_parrafo) > chunk_max:
            oraciones = _dividir_oraciones(parrafo)
            for oracion in oraciones:
                palabras_parrafo_inner = oracion.split()
                palabras_actuales, chunks = _acumular(
                    palabras_actuales, palabras_parrafo_inner,
                    chunks, chunk_size, chunk_max, overlap, min_words,
                )
        else:
            palabras_actuales, chunks = _acumular(
                palabras_actuales, palabras_parrafo,
                chunks, chunk_size, chunk_max, overlap, min_words,
            )

    # Guardar el último fragmento si tiene suficiente contenido
    if len(palabras_actuales) >= min_words:
        chunks.append(" ".join(palabras_actuales))

    return chunks


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    texto = re.sub(r"\r\n", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _dividir_parrafos(texto: str) -> list[str]:
    """Divide por doble salto de línea y filtra vacíos."""
    parrafos = [p.strip() for p in texto.split("\n\n")]
    return [p for p in parrafos if p and len(p.split()) >= 3]


def _dividir_oraciones(texto: str) -> list[str]:
    """Divide un párrafo largo en oraciones."""
    oraciones = re.split(r"(?<=[.!?])\s+", texto)
    return [o.strip() for o in oraciones if o.strip()]


def _acumular(
    palabras_actuales: list[str],
    palabras_nuevas: list[str],
    chunks: list[str],
    chunk_size: int,
    chunk_max: int,
    overlap: int,
    min_words: int,
) -> tuple[list[str], list[str]]:
    """Acumula palabras en el chunk actual; guarda y reinicia cuando se supera el máximo."""
    total = len(palabras_actuales) + len(palabras_nuevas)

    if total > chunk_max and len(palabras_actuales) >= min_words:
        # Guardar chunk actual
        chunks.append(" ".join(palabras_actuales))
        # Reiniciar con solapamiento
        palabras_actuales = palabras_actuales[-overlap:] + palabras_nuevas
    else:
        palabras_actuales = palabras_actuales + palabras_nuevas

    # Fragmento forzado si sigue siendo demasiado largo
    while len(palabras_actuales) > chunk_max:
        chunks.append(" ".join(palabras_actuales[:chunk_size]))
        palabras_actuales = palabras_actuales[chunk_size - overlap:]

    return palabras_actuales, chunks
