"""Servicio de ingesta: limpieza de texto plano, extracción desde URL y desde archivo.

Responsabilidades:
- Normalizar y sanear texto pegado directamente
- Extraer texto de una URL usando requests + BeautifulSoup4
- Extraer texto de un archivo PDF o TXT recibido en memoria (no se guarda)
- Validar la longitud del texto limpio con la regla única (utils.validacion_texto)
"""

import logging
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.core.exceptions import (
    ArchivoDemasiadoGrandeError,
    ArchivoNoPermitidoError,
    ExtraccionURLError,
    PdfSinTextoError,
)
from app.utils.pdf_extractor import extraer_texto_pdf_bytes
from app.utils.validacion_texto import (  # noqa: F401 (reexportadas)
    MAX_CARACTERES,
    MIN_CARACTERES,
    MIN_PALABRAS,
    validar_longitud_politica,
)

logger = logging.getLogger(__name__)

_TIMEOUT_HTTP = 10

TAMANO_MAXIMO_ARCHIVO = 5 * 1024 * 1024  # 5 MB

# Extensión → tipos de contenido aceptados para esa extensión.
TIPOS_ARCHIVO_PERMITIDOS: dict[str, set[str]] = {
    ".pdf": {"application/pdf", "application/x-pdf"},
    ".txt": {"text/plain"},
}

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


# ---------------------------------------------------------------------------
# Ingesta desde texto directo
# ---------------------------------------------------------------------------

def procesar_texto_directo(texto_raw: str) -> str:
    """Limpia y valida texto pegado por el usuario. Retorna texto normalizado."""
    texto = limpiar_texto(texto_raw)
    validar_longitud_politica(texto)
    logger.info("Texto directo aceptado [%d palabras].", len(texto.split()))
    return texto


# ---------------------------------------------------------------------------
# Ingesta desde URL
# ---------------------------------------------------------------------------

def _sitio(url: str) -> str:
    """Solo el nombre del sitio: los registros no guardan la dirección completa
    (puede incluir datos de la persona en la ruta o en los parámetros)."""
    return urlparse(url).hostname or "sitio desconocido"


def extraer_texto_url(url: str) -> str:
    """Descarga la URL y extrae el texto relevante. Retorna texto normalizado."""
    sitio = _sitio(url)
    logger.info("Extrayendo texto de %s.", sitio)
    try:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT_HTTP)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.warning("Timeout al acceder a %s", sitio)
        raise ExtraccionURLError("La URL tardó demasiado en responder.")
    except requests.exceptions.ConnectionError:
        logger.warning("No se pudo conectar a %s", sitio)
        raise ExtraccionURLError("No se pudo conectar a la URL proporcionada.")
    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP %s para %s", exc.response.status_code, sitio)
        raise ExtraccionURLError(
            f"La URL devolvió el estado HTTP {exc.response.status_code}."
        )
    except requests.exceptions.RequestException as exc:
        logger.error("Error inesperado al acceder a %s: %s", sitio, type(exc).__name__)
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

    validar_longitud_politica(texto)
    logger.info("Texto extraído de %s [%d palabras].", sitio, len(texto.split()))
    return texto


# ---------------------------------------------------------------------------
# Ingesta desde archivo (PDF o TXT)
# ---------------------------------------------------------------------------

def decodificar_txt(contenido: bytes) -> str:
    """UTF-8 (con o sin BOM) y, si no lo es, Windows-1252, habitual en archivos
    guardados en español desde Windows."""
    try:
        return contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        return contenido.decode("cp1252", errors="replace")


def procesar_archivo(nombre: str, tipo_contenido: str | None, contenido: bytes) -> str:
    """Valida el archivo, extrae su texto y lo normaliza. El archivo solo existe
    en memoria durante la solicitud: no se escribe en disco ni en la base."""
    extension = Path(nombre or "").suffix.lower()
    tipo = (tipo_contenido or "").split(";")[0].strip().lower()
    if extension not in TIPOS_ARCHIVO_PERMITIDOS or tipo not in TIPOS_ARCHIVO_PERMITIDOS[extension]:
        raise ArchivoNoPermitidoError()
    if len(contenido) > TAMANO_MAXIMO_ARCHIVO:
        raise ArchivoDemasiadoGrandeError()

    if extension == ".pdf":
        if not contenido.startswith(b"%PDF-"):
            raise ArchivoNoPermitidoError()
        texto_raw = extraer_texto_pdf_bytes(contenido, "archivo cargado")
        if not texto_raw.strip():
            raise PdfSinTextoError()
    else:
        texto_raw = decodificar_txt(contenido)

    texto = limpiar_texto(texto_raw)
    validar_longitud_politica(texto)
    logger.info("Archivo %s aceptado [%d palabras].", extension, len(texto.split()))
    return texto
