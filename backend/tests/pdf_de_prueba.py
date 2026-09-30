"""PDF reales para las pruebas, generados en memoria con ReportLab."""

import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def pdf_con_texto(lineas: list[str]) -> bytes:
    buffer = io.BytesIO()
    lienzo = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for linea in lineas:
        lienzo.drawString(50, y, linea)
        y -= 14
        if y < 50:
            lienzo.showPage()
            y = 750
    lienzo.save()
    return buffer.getvalue()


def pdf_sin_texto() -> bytes:
    """PDF con solo un dibujo, como un documento escaneado sin capa de texto."""
    buffer = io.BytesIO()
    lienzo = canvas.Canvas(buffer, pagesize=letter)
    lienzo.rect(100, 100, 300, 300, fill=1)
    lienzo.save()
    return buffer.getvalue()


LINEAS_POLITICA = [
    "Politica de privacidad de la aplicacion de ejemplo.",
    "Recopilamos su nombre, correo electronico y datos de uso del servicio.",
    "Utilizamos esta informacion para operar y mejorar la plataforma.",
    "Compartimos datos con proveedores que nos ayudan a prestar el servicio.",
    "Conservamos la informacion mientras su cuenta permanezca activa.",
    "Puede solicitar el acceso, la correccion o la eliminacion de sus datos.",
    "Notificaremos cualquier cambio importante en esta politica por correo.",
]
