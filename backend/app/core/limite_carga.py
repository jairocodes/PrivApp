"""Rechazo temprano de cargas de archivo demasiado grandes.

FastAPI procesa el formulario multipart antes de ejecutar la ruta, así que el
tamaño se revisa aquí, a partir de la cabecera Content-Length, antes de leer
el cuerpo: un envío enorme se rechaza sin llegar a memoria ni a disco. Las
solicitudes sin Content-Length (envío por fragmentos) siguen limitadas por el
proxy de la plataforma y por la validación de tamaño de la propia ruta.
"""

import json

from starlette.types import ASGIApp, Receive, Scope, Send

# Rutas que reciben archivos: la ingesta de la persona usuaria y la carga de
# documentos al corpus desde la administración (ambas con tope de 5 MB).
RUTAS_CARGA_ARCHIVO = frozenset({"/api/ingesta/archivo", "/api/admin/corpus"})
DETALLE_ARCHIVO_GRANDE = "El archivo supera el tamaño máximo de 5 MB."


class LimiteCargaArchivoMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("method") == "POST" and scope["path"] in RUTAS_CARGA_ARCHIVO:
            longitud = dict(scope["headers"]).get(b"content-length")
            if longitud is not None and longitud.isdigit() and int(longitud) > self.max_bytes:
                cuerpo = json.dumps({"detail": DETALLE_ARCHIVO_GRANDE}).encode()
                await send({
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(cuerpo)).encode()),
                        (b"connection", b"close"),
                    ],
                })
                await send({"type": "http.response.body", "body": cuerpo})
                return
        await self.app(scope, receive, send)
