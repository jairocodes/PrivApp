"""Expresiones SQL portables entre PostgreSQL y SQLite (pruebas).

- json_texto: lectura de un valor de texto dentro de una columna JSON
  (analysis_temp.resultado es JSONB en PostgreSQL y texto en SQLite).
- sin_acentos: texto sin acentos para búsquedas (extensión unaccent en
  PostgreSQL, migración 0007; función equivalente registrada en SQLite).
"""

import unicodedata

from sqlalchemy import event
from sqlalchemy.engine import Engine
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


class sin_acentos(FunctionElement):
    """sin_acentos(expresion) → el mismo texto sin tildes ni diéresis ("Política" → "Politica")."""

    type = String()
    inherit_cache = True


@compiles(sin_acentos, "postgresql")
def _sin_acentos_postgresql(elemento, compilador, **kw):
    return f"unaccent({compilador.process(elemento.clauses, **kw)})"


@compiles(sin_acentos, "sqlite")
def _sin_acentos_sqlite(elemento, compilador, **kw):
    return f"sin_acentos({compilador.process(elemento.clauses, **kw)})"


def quitar_acentos(texto: str | None) -> str | None:
    """Equivalente en Python de unaccent: descompone y quita las marcas diacríticas."""
    if texto is None:
        return None
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


@event.listens_for(Engine, "connect")
def _registrar_sin_acentos_en_sqlite(conexion_dbapi, _registro) -> None:
    # Solo SQLite (pruebas) necesita la función; PostgreSQL usa unaccent.
    if "sqlite" in type(conexion_dbapi).__module__:
        conexion_dbapi.create_function("sin_acentos", 1, quitar_acentos, deterministic=True)


def patron_contiene(texto: str) -> str:
    """Patrón LIKE que busca el texto literal (usar con escape="\\"): los
    comodines % y _ que escriba la persona no actúan como comodines."""
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"
