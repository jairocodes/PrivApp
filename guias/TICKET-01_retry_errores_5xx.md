# TICKET-01 — Conectar `_es_error_reintentable` al decorador `@retry`

**Prioridad:** Alta (rápido, alto valor)
**Complejidad:** Baja
**Área:** Backend — adaptador del proveedor de modelo de lenguaje
**Requiere decisión humana:** No
**Dependencias:** Ninguna

---

## Situación actual

En `backend/app/services/llm/openai_adapter.py`:

- La llamada al proveedor OpenAI está envuelta por un decorador `@retry` de la librería **tenacity**, configurado con `stop_after_attempt(3)` y `wait_exponential(multiplier=2, min=2, max=10)`.
- Ese decorador está configurado para reintentar **solo** ante `RateLimitError` y `APIConnectionError`.
- Existe además una función auxiliar llamada `_es_error_reintentable` que **sí** contempla como reintentable un `APIStatusError` con código de estado ≥ 500 (errores de servidor del proveedor, 5xx), **pero esa función no está conectada al decorador `@retry`**. Es decir, hoy los errores 5xx del proveedor **no se reintentan**, a pesar de que la lógica para reconocerlos ya existe.

## Objetivo

Hacer que la política de reintentos del decorador `@retry` use `_es_error_reintentable` como criterio, de modo que se reintente ante errores transitorios de conexión, límite de tasa **y** errores de servidor 5xx del proveedor, de forma unificada y coherente.

## Qué hacer

1. Localiza en `openai_adapter.py` la definición de `_es_error_reintentable` y el decorador `@retry` que envuelve la función de llamada al proveedor.
2. Cambia la condición de reintento del decorador para que use `_es_error_reintentable` en lugar de la lista fija de tipos de excepción. Con tenacity, esto normalmente se hace con `retry=retry_if_exception(_es_error_reintentable)` en vez de `retry=retry_if_exception_type((RateLimitError, APIConnectionError))`.
3. Asegúrate de que `_es_error_reintentable` devuelva `True` para `RateLimitError`, `APIConnectionError` y `APIStatusError` con `status_code >= 500`, y `False` para el resto (autenticación, modelo inválido, etc.). Si ya cubre estos casos, no la modifiques; solo conéctala. Si le falta alguno de los dos primeros, complétala para que el comportamiento nuevo sea un superconjunto correcto del actual (no debe dejar de reintentar nada que hoy sí se reintente).
4. Verifica que los errores **no** reintentables sigan envolviéndose en `LLMError` (HTTP 502) sin reintentar, tal como hoy.

## Criterios de aceptación

- Un `APIStatusError` con `status_code >= 500` provoca reintentos (hasta 3 intentos con backoff exponencial), en lugar de fallar al primer intento.
- `RateLimitError` y `APIConnectionError` siguen provocando reintentos exactamente como antes (no hay regresión).
- Un error de autenticación o de modelo inválido (no 5xx) **no** se reintenta y se traduce a `LLMError` (502).
- La suite de pruebas completa sigue en verde.
- Se agrega al menos una prueba unitaria que verifique que un error 5xx del proveedor dispara reintentos (puedes simular el adaptador para que lance `APIStatusError` con `status_code=503` las primeras dos veces y responda bien a la tercera, y comprobar que el resultado final es exitoso). Si ya existe una prueba equivalente, no la dupliques; menciónalo en el reporte.

## Fuera de alcance

- No cambies los parámetros de backoff (`multiplier`, `min`, `max`, número de intentos).
- No toques el adaptador de Gemini salvo que comparta exactamente la misma función y el mismo problema; si es el caso, indícalo en el reporte y **pregunta** antes de replicar el cambio ahí (podría abordarse en un ticket aparte para mantener la atomicidad).
