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


MENSAJE_DECLARACION_EDAD = (
    "Debes declarar que eres mayor de 18 años o que cuentas con el consentimiento "
    "de tu madre, padre o persona encargada."
)


class DeclaracionEdadFaltanteError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=MENSAJE_DECLARACION_EDAD,
        )


class AvisoNoAceptadoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes aceptar el aviso de privacidad para registrarte.",
        )


class PasswordActualIncorrectaError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta.",
        )


class PasswordRepetidaError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser distinta de la actual.",
        )


class AccesoDenegadoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso.",
        )


class AutodesactivacionError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta.",
        )


class PasswordIncorrectaError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña es incorrecta.",
        )


class UltimoAdministradorError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu cuenta porque eres el único administrador activo.",
        )


class CuentaConAnalisisEnCursoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Espera a que termine el análisis en curso antes de eliminar tu cuenta.",
        )


class TextoDemasiadoCortoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El texto debe tener al menos 200 caracteres y 40 palabras.",
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


class ArchivoNoPermitidoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt).",
        )


class ArchivoDemasiadoGrandeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el tamaño máximo de 5 MB.",
        )


class PdfSinTextoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No se encontró texto en el PDF. Si es un documento escaneado, el sistema "
                "no puede leerlo: copia el texto de la política y pégalo directamente."
            ),
        )


class DocumentoCorpusNoEncontradoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado en el corpus normativo.",
        )


class DocumentoCorpusDuplicadoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un documento con ese nombre en el corpus normativo.",
        )


class DocumentoCorpusSinTextoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El documento no contiene texto suficiente para incorporarlo al corpus (mínimo 50 palabras).",
        )


class RangoFechasInvalidoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha inicial no puede ser posterior a la fecha final.",
        )


class AnalisisEnCursoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un análisis que todavía se está procesando.",
        )


class AnalisisEnProcesoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="El análisis todavía se está procesando.",
        )


class AnalisisFallidoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="El análisis no pudo completarse. Intenta analizar la política de nuevo.",
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
