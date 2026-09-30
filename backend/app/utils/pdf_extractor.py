"""Extracción de texto desde archivos PDF.

Usa pdfplumber como primera opción (mejor preservación de estructura).
pypdf actúa como fallback si pdfplumber falla.

Acepta una ruta en disco (carga del corpus normativo) o el contenido en
memoria (archivos que sube el usuario, que nunca se escriben en disco).
"""

import io
import logging
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

FuentePdf = Path | BinaryIO


def extraer_texto_pdf(ruta: Path | str) -> str:
    """Extrae el texto completo de un PDF en disco. Devuelve string vacío si falla."""
    ruta = Path(ruta)
    if not ruta.exists():
        logger.error("Archivo no encontrado: %s", ruta)
        return ""

    texto = _extraer_con_pdfplumber(ruta)
    if texto:
        return texto

    logger.warning("pdfplumber no produjo texto en %s, intentando pypdf.", ruta.name)
    return _extraer_con_pypdf(ruta)


def extraer_texto_pdf_bytes(contenido: bytes, nombre: str = "archivo.pdf") -> str:
    """Extrae el texto de un PDF recibido en memoria. Devuelve string vacío si
    el PDF no tiene texto extraíble (por ejemplo, escaneado) o no se puede leer."""
    texto = _extraer_con_pdfplumber(io.BytesIO(contenido), nombre)
    if texto:
        return texto

    logger.warning("pdfplumber no produjo texto en %s, intentando pypdf.", nombre)
    return _extraer_con_pypdf(io.BytesIO(contenido), nombre)


def _nombre(fuente: FuentePdf, nombre: str | None) -> str:
    if nombre:
        return nombre
    return fuente.name if isinstance(fuente, Path) else "archivo.pdf"


def _extraer_con_pdfplumber(fuente: FuentePdf, nombre: str | None = None) -> str:
    nombre = _nombre(fuente, nombre)
    try:
        import pdfplumber

        paginas = []
        with pdfplumber.open(fuente) as pdf:
            for i, pagina in enumerate(pdf.pages, 1):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    paginas.append(texto_pagina)
                else:
                    logger.debug("Página %d sin texto en %s.", i, nombre)

        texto = "\n\n".join(paginas).strip()
        if texto:
            logger.info("pdfplumber extrajo %d palabras de %s.", len(texto.split()), nombre)
        return texto
    except Exception as exc:
        logger.warning("pdfplumber falló para %s: %s", nombre, exc)
        return ""


def _extraer_con_pypdf(fuente: FuentePdf, nombre: str | None = None) -> str:
    nombre = _nombre(fuente, nombre)
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(fuente) if isinstance(fuente, Path) else fuente)
        paginas = []
        for pagina in reader.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                paginas.append(texto_pagina)

        texto = "\n\n".join(paginas).strip()
        if texto:
            logger.info("pypdf extrajo %d palabras de %s.", len(texto.split()), nombre)
        return texto
    except Exception as exc:
        logger.error("pypdf falló para %s: %s", nombre, exc)
        return ""
