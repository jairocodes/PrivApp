"""Pruebas de los adaptadores LLM: política de reintentos."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from openai import APIStatusError

from app.services.llm.openai_adapter import OpenAIAdapter


def _api_status_error(status_code: int) -> APIStatusError:
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx.Response(status_code=status_code, request=request)
    return APIStatusError("error del proveedor", response=response, body=None)


class TestRetryOpenAIAdapter:
    async def test_error_5xx_dispara_reintentos_y_termina_en_exito(self):
        """Un APIStatusError 503 en los dos primeros intentos no debe propagar
        el fallo: al tercer intento responde bien y el resultado es exitoso."""
        adapter = OpenAIAdapter(api_key="fake-key")

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="respuesta ok"))]

        with patch.object(
            adapter._client.chat.completions,
            "create",
            AsyncMock(
                side_effect=[
                    _api_status_error(503),
                    _api_status_error(503),
                    mock_response,
                ]
            ),
        ) as mock_create, patch("asyncio.sleep", AsyncMock()):
            resultado = await adapter.generar_analisis(
                system_prompt="system",
                texto_seccion="texto",
                contexto_normativo="",
            )

        assert resultado == "respuesta ok"
        assert mock_create.call_count == 3

    async def test_error_4xx_no_reintenta_y_se_traduce_a_llmerror(self):
        """Un error no reintentable (4xx) falla en el primer intento, sin
        reintentos, y se traduce a LLMError."""
        from app.core.exceptions import LLMError

        adapter = OpenAIAdapter(api_key="fake-key")

        with patch.object(
            adapter._client.chat.completions,
            "create",
            AsyncMock(side_effect=_api_status_error(400)),
        ) as mock_create:
            with pytest.raises(LLMError):
                await adapter.generar_analisis(
                    system_prompt="system",
                    texto_seccion="texto",
                    contexto_normativo="",
                )

        assert mock_create.call_count == 1
