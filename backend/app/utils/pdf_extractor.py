"""Extracción de texto desde archivos PDF.

Usa pdfplumber como primera opción (mejor preservación de estructura).
pypdf actúa como fallback si pdfplumber falla.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extraer_texto_pdf(ruta: Path | str) -> str:
    """Extrae el texto completo de un PDF. Devuelve string vacío si falla."""
    ruta = Path(ruta)
    if not ruta.exists():
        logger.error("Archivo no encontrado: %s", ruta)
        return ""

    texto = _extraer_con_pdfplumber(ruta)
    if texto:
        return texto

    logger.warning("pdfplumber no produjo texto en %s, intentando pypdf.", ruta.name)
    return _extraer_con_pypdf(ruta)


def _extraer_con_pdfplumber(ruta: Path) -> str:
    try:
        import pdfplumber

        paginas = []
        with pdfplumber.open(ruta) as pdf:
            for i, pagina in enumerate(pdf.pages, 1):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    paginas.append(texto_pagina)
                else:
                    logger.debug("Página %d sin texto en %s.", i, ruta.name)

        texto = "\n\n".join(paginas).strip()
        if texto:
            logger.info("pdfplumber extrajo %d palabras de %s.", len(texto.split()), ruta.name)
        return texto
    except Exception as exc:
        logger.warning("pdfplumber falló para %s: %s", ruta.name, exc)
        return ""


def _extraer_con_pypdf(ruta: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(ruta))
        paginas = []
        for pagina in reader.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                paginas.append(texto_pagina)

        texto = "\n\n".join(paginas).strip()
        if texto:
            logger.info("pypdf extrajo %d palabras de %s.", len(texto.split()), ruta.name)
        return texto
    except Exception as exc:
        logger.error("pypdf falló para %s: %s", ruta.name, exc)
        return ""
