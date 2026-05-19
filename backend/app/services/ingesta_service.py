"""Servicio de ingesta: limpieza de texto plano y extracción desde URL.

Responsabilidades:
- Normalizar y sanear texto pegado directamente
- Extraer texto de una URL usando requests + BeautifulSoup4
- Validar longitudes mínima/máxima antes de devolver
"""

import logging
import re
import unicodedata

import requests
from bs4 import BeautifulSoup

from app.core.exceptions import (
    ExtraccionURLError,
    TextoDemasiadoCortoError,
    TextoDemasiadoLargoError,
)

logger = logging.getLogger(__name__)

MIN_PALABRAS = 40
MAX_CARACTERES = 50_000
_TIMEOUT_HTTP = 10

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; PrivAppBot/1.0; "
        "+https://privapp.example.com/bot)"
    )
}


# ---------------------------------------------------------------------------
# Limpieza de texto
# ---------------------------------------------------------------------------

def limpiar_texto(texto: str) -> str:
    """Normaliza espacios, elimina caracteres de control y normaliza unicode."""
    texto = unicodedata.normalize("NFC", texto)
    texto = "".join(
        c for c in texto if unicodedata.category(c) not in ("Cc", "Cf") or c in "\n\r\t"
    )
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in texto.splitlines()]
    texto = "\n".join(lines)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _validar_longitud(texto: str) -> None:
    palabras = len(texto.split())
    if palabras < MIN_PALABRAS:
        raise TextoDemasiadoCortoError()
    if len(texto) > MAX_CARACTERES:
        raise TextoDemasiadoLargoError()


# ---------------------------------------------------------------------------
# Ingesta desde texto directo
# ---------------------------------------------------------------------------

def procesar_texto_directo(texto_raw: str) -> str:
    """Limpia y valida texto pegado por el usuario. Retorna texto normalizado."""
    texto = limpiar_texto(texto_raw)
    _validar_longitud(texto)
    logger.info("Texto directo aceptado [%d palabras].", len(texto.split()))
    return texto


# ---------------------------------------------------------------------------
# Ingesta desde URL
# ---------------------------------------------------------------------------

def extraer_texto_url(url: str) -> str:
    """Descarga la URL y extrae el texto relevante. Retorna texto normalizado."""
    logger.info("Extrayendo texto de URL: %s", url)
    try:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT_HTTP)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.warning("Timeout al acceder a %s", url)
        raise ExtraccionURLError("La URL tardó demasiado en responder.")
    except requests.exceptions.ConnectionError:
        logger.warning("No se pudo conectar a %s", url)
        raise ExtraccionURLError("No se pudo conectar a la URL proporcionada.")
    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP %s para %s", exc.response.status_code, url)
        raise ExtraccionURLError(
            f"La URL devolvió el estado HTTP {exc.response.status_code}."
        )
    except requests.exceptions.RequestException as exc:
        logger.error("Error inesperado al acceder a %s: %s", url, exc)
        raise ExtraccionURLError("Error al acceder a la URL.") from exc

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        raise ExtraccionURLError(
            "La URL no devolvió contenido HTML. "
            f"Tipo recibido: {content_type.split(';')[0].strip()}"
        )

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    contenedor = soup.find("main") or soup.find("article") or soup.body
    if contenedor is None:
        raise ExtraccionURLError("No se encontró contenido de texto en la página.")

    texto_raw = contenedor.get_text(separator="\n")
    texto = limpiar_texto(texto_raw)

    if not texto:
        raise ExtraccionURLError("La página no contiene texto extraíble.")

    _validar_longitud(texto)
    logger.info("Texto extraído de '%s' [%d palabras].", url, len(texto.split()))
    return texto
