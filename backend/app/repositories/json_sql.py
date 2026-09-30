"""Lectura de un valor de texto dentro de una columna JSON, portable entre motores.

analysis_temp.resultado es JSONB en PostgreSQL y texto en SQLite (pruebas), así
que el acceso por ruta se compila distinto en cada uno.
"""

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.types import String


class json_texto(FunctionElement):
    """json_texto(columna, "clave", "subclave") → el valor en esa ruta, como texto."""

    type = String()
    inherit_cache = True

    def __init__(self, columna, *ruta: str):
        self.ruta = ruta
        super().__init__(columna)


@compiles(json_texto, "postgresql")
def _json_texto_postgresql(elemento, compilador, **kw):
    columna = compilador.process(elemento.clauses, **kw)
    ruta = "{" + ",".join(elemento.ruta) + "}"
    return f"({columna} #>> '{ruta}')"


@compiles(json_texto, "sqlite")
def _json_texto_sqlite(elemento, compilador, **kw):
    columna = compilador.process(elemento.clauses, **kw)
    ruta = "$." + ".".join(elemento.ruta)
    return f"json_extract({columna}, '{ruta}')"
