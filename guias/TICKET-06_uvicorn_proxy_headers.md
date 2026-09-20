# TICKET-06 — Configurar Uvicorn para confiar en las cabeceras de reenvío del proxy (HTTPS)

**Prioridad:** Media (correctitud de HTTPS en producción)
**Complejidad:** Baja
**Área:** Backend / despliegue — arranque del servidor
**Requiere decisión humana:** Parcial (una verificación de seguridad, ver abajo)
**Dependencias:** Ninguna

---

## Contexto (verificado)

Según la documentación oficial de Railway (consultada en septiembre de 2026):
- Railway termina el TLS/HTTPS en su **proxy inverso (edge)** y reenvía la petición al contenedor de la aplicación como **HTTP plano** internamente.
- Railway inyecta la cabecera `X-Forwarded-Proto` (que indica `https` para el tráfico original) y otras cabeceras de reenvío.

**Problema:** por defecto, Uvicorn solo confía en las cabeceras de reenvío cuando provienen de `127.0.0.1`. Como el proxy de Railway no es `127.0.0.1` desde la perspectiva del contenedor, sin configuración adicional la aplicación puede **no** reconocer que la petición original llegó por HTTPS. Esto puede causar, por ejemplo, que FastAPI genere URLs de redirección con esquema `http://` en lugar de `https://`, o que cualquier lógica que dependa del esquema de la petición se comporte incorrectamente.

## Objetivo

Configurar el arranque de Uvicorn para que reconozca correctamente el protocolo original (`https`) a partir de las cabeceras de reenvío emitidas por el proxy de Railway.

## Qué hacer

1. Localiza cómo se arranca Uvicorn en producción. Puede estar en:
   - El `Dockerfile` del backend (comando `CMD`/`ENTRYPOINT`).
   - Un script de arranque.
   - La configuración de inicio en Railway (variable de comando de arranque), si aplica.
   Verifica cuál es el punto real de arranque antes de editar.
2. Añade al comando de arranque de Uvicorn las banderas:
   - `--proxy-headers`
   - `--forwarded-allow-ips='*'`  (o la IP/rango específico del proxy interno de Railway, si puede determinarse con certeza; ver la nota de seguridad).
3. Si el arranque se hace programáticamente (`uvicorn.run(...)` en Python), usa los parámetros equivalentes: `proxy_headers=True`, `forwarded_allow_ips="*"`.

## ⚠️ Nota de seguridad (verificación requerida)

Usar `--forwarded-allow-ips='*'` significa "confía en las cabeceras `X-Forwarded-*` de cualquier origen". **Esto solo es seguro si el contenedor NO es accesible directamente desde internet**, es decir, si la única forma de llegar al contenedor es a través del proxy de Railway. Si el contenedor fuera accesible directamente, un atacante podría falsificar `X-Forwarded-Proto`.

Antes de fijar `'*'`, **confirma con el responsable del proyecto** que en la configuración de red de Railway el servicio del backend solo se expone a través del proxy (que es el comportamiento estándar de Railway para servicios con dominio público, pero conviene confirmarlo). Si se puede determinar la IP/rango concreto del proxy interno, es preferible usar ese valor en lugar de `'*'`. Documenta en el reporte qué valor se usó y por qué.

## Criterios de aceptación

- El comando de arranque de Uvicorn incluye `--proxy-headers` y un valor apropiado de `--forwarded-allow-ips`.
- Tras el despliegue, la aplicación reconoce el esquema `https` para las peticiones entrantes (por ejemplo, las URLs absolutas que genere el backend, si las hay, usan `https://`).
- No se introduce ninguna credencial ni valor sensible en el repositorio.
- La suite de pruebas sigue en verde (este cambio no debería afectar a las pruebas, que corren fuera del proxy; si algo se rompe, repórtalo).

## Fuera de alcance

- No cambies la configuración de TLS en sí (los certificados los gestiona Railway automáticamente; no hay que tocar nada de certificados en el código).
- No añadas un proxy inverso propio (Nginx/Caddy) dentro del contenedor; sería redundante con el de Railway y está fuera de este ticket.
