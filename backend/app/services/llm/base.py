"""Interfaz abstracta del adaptador LLM (patrón Adapter/Strategy).

Permite sustituir el proveedor del modelo de lenguaje sin modificar la
lógica del motor de análisis.
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
        esquema: dict | None = None,
    ) -> str:
        """Envía el prompt al LLM y devuelve la respuesta como string JSON.

        Args:
            system_prompt: Instrucciones del sistema para el LLM.
            texto_seccion: Fragmento de la política a analizar.
            contexto_normativo: Fragmentos normativos recuperados por RAG.
            esquema: Esquema JSON que la respuesta debe cumplir, con el formato
                {"name": ..., "schema": {...}}. Si el proveedor lo admite, lo
                impone al generar; si no, basta con pedir JSON.

        Returns:
            Respuesta del LLM en formato JSON string.
        """
        ...
