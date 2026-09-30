"""Configuración de los registros del servidor sin datos personales.

- Los mensajes propios no incluyen correos, nombres de archivo ni direcciones
  web completas (ver auth_service e ingesta_service).
- SlowAPI escribe la IP al rechazar una solicitud por exceso: se reemplaza.
- El registro de acceso de uvicorn (una línea con la IP por solicitud) se
  desactiva en producción con --no-access-log (ver Dockerfile).
"""

import logging

IP_OMITIDA = "[ip omitida]"


class OcultarIpLimitador(logging.Filter):
    """Reemplaza la clave del limitador (la IP) en el aviso 'ratelimit ... exceeded'."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple) and len(record.args) >= 2 and str(record.msg).startswith("ratelimit"):
            args = list(record.args)
            args[1] = IP_OMITIDA
            record.args = tuple(args)
        return True


def configurar_registro(nivel: str) -> None:
    logging.basicConfig(
        level=getattr(logging, nivel.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    registro_limitador = logging.getLogger("slowapi")
    if not any(isinstance(f, OcultarIpLimitador) for f in registro_limitador.filters):
        registro_limitador.addFilter(OcultarIpLimitador())
