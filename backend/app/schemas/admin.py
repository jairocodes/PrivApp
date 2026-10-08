"""Schemas Pydantic de la administración de usuarios.

Minimización de datos: el listado expone solo datos de la cuenta, nunca el
contenido de los análisis del usuario.
"""

from datetime import datetime

from pydantic import BaseModel


class UsuarioAdminItem(BaseModel):
    id: int
    nombre: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CambioEstadoUsuarioRequest(BaseModel):
    activo: bool


class ListadoUsuariosResponse(BaseModel):
    items: list[UsuarioAdminItem]
    total: int
    page: int
    page_size: int
