"""Excepciones personalizadas de la aplicación."""

from fastapi import HTTPException, status


class CredencialesInvalidasError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class UsuarioNoEncontradoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )


class UsuarioYaExisteError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado.",
        )


class TokenInvalidoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class AccesoDenegadoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso.",
        )


class TextoDemasiadoCortoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El texto debe tener al menos 200 caracteres.",
        )


class TextoDemasiadoLargoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El texto no puede exceder los 200,000 caracteres.",
        )


class ExtraccionURLError(HTTPException):
    def __init__(self, detalle: str = "No fue posible extraer texto de la URL proporcionada."):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detalle,
        )


class LLMError(HTTPException):
    def __init__(self, detalle: str = "Error al comunicarse con el modelo de lenguaje."):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detalle,
        )


class AnalisisNoEncontradoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis no encontrado.",
        )
