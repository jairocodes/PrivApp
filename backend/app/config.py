"""Configuración centralizada de la aplicación mediante variables de entorno."""

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # OpenAI (proveedor del modelo de lenguaje)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # General
    environment: str = "development"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
