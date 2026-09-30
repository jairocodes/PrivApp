"""Regla única de longitud para el texto de una política (todas las vías de ingesta).

Se aplica siempre sobre el texto ya limpiado y normalizado: mínimo 200
caracteres y 40 palabras, máximo 200,000 caracteres.
"""

from app.core.exceptions import TextoDemasiadoCortoError, TextoDemasiadoLargoError

MIN_CARACTERES = 200
MIN_PALABRAS = 40
MAX_CARACTERES = 200_000

# Tope del texto crudo recibido, antes de limpiarlo. Solo evita procesar
# entradas desproporcionadas: la regla real se valida tras la limpieza, que
# puede reducir mucho la longitud (espacios y saltos de línea repetidos).
MAX_CARACTERES_ENTRADA = 2 * MAX_CARACTERES


def validar_longitud_politica(texto: str) -> None:
    """Lanza TextoDemasiadoCortoError o TextoDemasiadoLargoError si el texto
    limpio no cumple la regla de longitud."""
    if len(texto) > MAX_CARACTERES:
        raise TextoDemasiadoLargoError()
    if len(texto) < MIN_CARACTERES or len(texto.split()) < MIN_PALABRAS:
        raise TextoDemasiadoCortoError()
