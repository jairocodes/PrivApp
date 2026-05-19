"""Adaptador para Google Gemini. Implementación completa en Sprint 3.

Implementa LLMAdapter usando el SDK google-generativeai.
Incluye reintentos con backoff exponencial (tenacity).
"""

from app.services.llm.base import LLMAdapter


class GeminiAdapter(LLMAdapter):
    """Adaptador concreto para Google Gemini API."""

    # TODO Sprint 3: implementar
    # - __init__(model, api_key)
    # - generar_analisis(system_prompt, texto_seccion, contexto_normativo) -> str
    # - Manejo de reintentos con tenacity (max 3, backoff exponencial)
    # - Logging de llamadas (sin exponer API key)

    async def generar_analisis(
        self,
        system_prompt: str,
        texto_seccion: str,
        contexto_normativo: str,
    ) -> str:
        raise NotImplementedError("GeminiAdapter será implementado en Sprint 3.")
