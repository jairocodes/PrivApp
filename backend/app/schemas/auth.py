"""Schemas Pydantic para autenticación."""

from pydantic import BaseModel, EmailStr, Field, field_validator


def validar_fortaleza_password(v: str) -> str:
    """Reglas de fortaleza compartidas por el registro y el cambio de contraseña
    (la longitud mínima de 8 caracteres se declara en cada Field)."""
    if not any(c.isupper() for c in v):
        raise ValueError("Debe contener al menos una letra mayúscula.")
    if not any(c.isdigit() for c in v):
        raise ValueError("Debe contener al menos un número.")
    return v


class RegisterRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    acepta_aviso: bool

    @field_validator("acepta_aviso")
    @classmethod
    def validate_acepta_aviso(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Debes aceptar el aviso de privacidad para registrarte.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validar_fortaleza_password(v)


class ActualizarPerfilRequest(BaseModel):
    """Solo el nombre es editable; el correo no se modifica."""

    model_config = {"str_strip_whitespace": True}

    nombre: str = Field(..., min_length=2, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    nombre: str
    email: str
    role: str

    model_config = {"from_attributes": True}
