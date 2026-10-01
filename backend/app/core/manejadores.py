"""Respuestas de error con el mismo formato que el resto de la API ({"detail": ...})."""

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

MENSAJE_LIMITE_SUPERADO = "Demasiadas solicitudes. Espera un minuto antes de volver a intentarlo."
_PREFIJO_PYDANTIC = "Value error, "


async def manejar_limite_superado(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Como el manejador de SlowAPI (agrega las cabeceras del límite si el
    limitador las tiene activadas), pero con un mensaje en español en «detail»."""
    respuesta = JSONResponse({"detail": MENSAJE_LIMITE_SUPERADO}, status_code=429)
    return request.app.state.limiter._inject_headers(respuesta, request.state.view_rate_limit)


async def manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Mismo formato que FastAPI, sin el prefijo «Value error, » que Pydantic
    antepone a los mensajes de las validaciones propias."""
    errores = []
    for error in exc.errors():
        error = dict(error)
        mensaje = error.get("msg")
        if isinstance(mensaje, str) and mensaje.startswith(_PREFIJO_PYDANTIC):
            error["msg"] = mensaje[len(_PREFIJO_PYDANTIC):]
        errores.append(error)
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errores)})
