"""Adaptador para Google Gemini usando el patrón Adapter definido en base.py.

Usa google-generativeai SDK con reintentos exponenciales (tenacity).
El API key se lee de la configuración de entorno — nunca se loguea.
"""

import logging

import google.generativeai as genai
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import LLMError
from app.services.llm.base import LLMAdapter

logger = logging.getLogger(__name__)

_RETRYABLE = (Exception,)


def _es_error_reintentable(exc: BaseException) -> bool:
    """Reintenta en errores transitorios de red/cuota; no en errores de autenticación."""
    if isinstance(exc, LLMError):
        # Ya fue clasificado como no reintentable dentro de generar_analisis.
        return False
    msg = str(exc).lower()
    no_reintentar = ("api_key", "permission", "invalid", "not found", "quota exceeded permanently")
    return not any(s in msg for s in no_reintentar)


class GeminiAdapter(LLMAdapter):
    """Adaptador concreto para Google Gemini API."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        genai.configure(api_key=api_key)
        self._model_name = model
        logger.info("GeminiAdapter inicializado con modelo '%s'.", model)

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
    ) -> str:
        """Envía el prompt a Gemini y retorna el texto generado."""
        prompt_usuario = (
            f"CONTEXTO NORMATIVO:\n{contexto_normativo}\n\n"
            f"SECCIÓN A ANALIZAR:\n{texto_seccion}"
        )

        try:
            modelo = genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=system_prompt,
            )
            logger.debug(
                "Llamando a Gemini [modelo=%s, chars_usuario=%d].",
                self._model_name,
                len(prompt_usuario),
            )
            respuesta = await modelo.generate_content_async(prompt_usuario)
            texto = respuesta.text.strip()
            logger.info(
                "Gemini respondió [modelo=%s, chars_respuesta=%d].",
                self._model_name,
                len(texto),
            )
            return texto
        except Exception as exc:
            if not _es_error_reintentable(exc):
                logger.error("Error no reintentable en Gemini: %s", type(exc).__name__)
                raise LLMError(f"Error en Gemini: {type(exc).__name__}") from exc
            logger.warning("Error transitorio en Gemini (%s). Reintentando...", type(exc).__name__)
            raise
