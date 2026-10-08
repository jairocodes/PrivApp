"""Adaptador para OpenAI usando el patrón Adapter definido en base.py.

Usa el SDK openai con reintentos exponenciales (tenacity).
El API key se lee de la configuración de entorno — nunca se loguea.
"""

import logging

from openai import AsyncOpenAI, APIStatusError, RateLimitError, APIConnectionError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import LLMError
from app.services.llm.base import LLMAdapter

logger = logging.getLogger(__name__)


def _es_error_reintentable(exc: BaseException) -> bool:
    """Reintenta en rate limit y errores de red; no en errores de autenticación o modelo."""
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIConnectionError):
        return True
    if isinstance(exc, APIStatusError):
        # 429 y 5xx son reintentables; 4xx no
        return exc.status_code >= 500
    return False


class OpenAIAdapter(LLMAdapter):
    """Adaptador concreto para OpenAI API (gpt-4o-mini, gpt-4o, etc.)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        seed: int | None = None,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model_name = model
        self.temperatura = temperature
        self.semilla = seed
        # Configuraciones del servidor de OpenAI que atendieron las llamadas
        # (system_fingerprint): si cambian, la misma semilla puede dar otra respuesta.
        self.huellas_sistema: set[str] = set()
        logger.info("OpenAIAdapter inicializado con modelo '%s'.", model)

    @property
    def modelo(self) -> str:
        return self._model_name

    @retry(
        retry=retry_if_exception(_es_error_reintentable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    async def generar_analisis(
        self,
        system_prompt: str,
        texto_seccion: str,
        contexto_normativo: str,
        esquema: dict | None = None,
    ) -> str:
        """Envía el prompt a OpenAI y retorna el texto generado.

        texto_seccion se usa como mensaje de usuario completo (pre-construido por el caller).
        contexto_normativo se ignora cuando ya está embebido en texto_seccion.
        Con `esquema`, la respuesta se genera con salidas estructuradas estrictas:
        OpenAI garantiza que cumple el esquema (campos, tipos y listas cerradas).
        """
        prompt_usuario = (
            texto_seccion
            if not contexto_normativo
            else f"CONTEXTO NORMATIVO:\n{contexto_normativo}\n\nSECCIÓN A ANALIZAR:\n{texto_seccion}"
        )

        try:
            logger.debug(
                "Llamando a OpenAI [modelo=%s, chars_usuario=%d].",
                self._model_name,
                len(prompt_usuario),
            )
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_usuario},
                ],
                temperature=self.temperatura,
                seed=self.semilla,
                response_format=(
                    {"type": "json_schema", "json_schema": {**esquema, "strict": True}}
                    if esquema
                    else {"type": "json_object"}
                ),
            )
            if response.system_fingerprint:
                self.huellas_sistema.add(response.system_fingerprint)
            texto = response.choices[0].message.content.strip()
            logger.info(
                "OpenAI respondió [modelo=%s, chars_respuesta=%d].",
                self._model_name,
                len(texto),
            )
            return texto
        except Exception as exc:
            if _es_error_reintentable(exc):
                logger.warning("Error transitorio en OpenAI (%s). Reintentando...", type(exc).__name__)
                raise
            logger.error("Error no reintentable en OpenAI: %s", type(exc).__name__)
            raise LLMError(f"Error en OpenAI: {type(exc).__name__}") from exc
