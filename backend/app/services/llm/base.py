"""Interfaz abstracta del adaptador LLM (patrón Adapter/Strategy).

Permite sustituir el proveedor de LLM (Gemini → Claude, GPT, etc.)
sin modificar la lógica del motor de análisis.
"""

from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """Contrato que debe cumplir cualquier adaptador de LLM."""

    @abstractmethod
    async def generar_analisis(
        self,
        system_prompt: str,
        texto_seccion: str,
        contexto_normativo: str,
    ) -> str:
        """Envía el prompt al LLM y devuelve la respuesta como string JSON.

        Args:
            system_prompt: Instrucciones del sistema para el LLM.
            texto_seccion: Fragmento de la política a analizar.
            contexto_normativo: Fragmentos normativos recuperados por RAG.

        Returns:
            Respuesta del LLM en formato JSON string.
        """
        ...
