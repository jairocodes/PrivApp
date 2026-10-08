"""Configuración centralizada de la aplicación mediante variables de entorno."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalizar_url_bd(url: str) -> str:
    """Usa el controlador asíncrono (asyncpg) aunque la URL llegue sin él.

    Railway entrega la conexión como ``postgresql://`` (o ``postgres://``), y
    SQLAlchemy asíncrono necesita ``postgresql+asyncpg://``.
    """
    for prefijo in ("postgresql://", "postgres://"):
        if url.startswith(prefijo):
            return "postgresql+asyncpg://" + url[len(prefijo):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos
    database_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Redis (lista de revocación de tokens JWT)
    redis_url: str

    # Proveedor activo del modelo de lenguaje (hoy solo "openai")
    llm_provider: str = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # Generación lo más reproducible posible: el mismo texto debe dar el mismo
    # resultado. OpenAI trata la semilla como "mejor esfuerzo", no como garantía.
    openai_temperature: float = 0.0
    openai_seed: int | None = 20261003

    # General
    environment: str = "development"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    # Registrar cada consulta SQL con sus parámetros: solo para depurar en local.
    sql_echo: bool = False

    @field_validator("database_url")
    @classmethod
    def _url_asincrona(cls, valor: str) -> str:
        return normalizar_url_bd(valor)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
