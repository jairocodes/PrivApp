# TICKET-03 — Invalidación real de sesión al cerrar sesión (logout)

**Prioridad:** Media
**Complejidad:** Media-Alta
**Área:** Backend — autenticación + infraestructura
**Requiere decisión humana:** **SÍ — no ejecutar sin aprobación (ver más abajo)**
**Dependencias:** Se beneficia de que el TICKET-02 (Repository) ya esté hecho si se elige la opción de persistencia en base de datos.

---

## Situación actual

En `backend/app/api/v1/auth.py` existe el endpoint `POST /api/auth/logout`, pero el cierre de sesión **solo ocurre del lado del cliente** (el cliente borra el token de `localStorage`). El token JWT sigue siendo válido en el servidor hasta su expiración natural (24 horas). Si alguien copió el token antes del logout, puede seguir usándolo.

Además, el sistema está diseñado como **stateless** (RE-01): el servidor no mantiene estado de sesión, para permitir múltiples instancias. Cualquier solución debe respetar ese principio en la medida de lo posible.

## Objetivo

Implementar una invalidación real de tokens al cerrar sesión, mediante una **lista de revocación**: al hacer logout, el identificador único del token (`jti`) se registra como revocado, con una expiración automática igual al tiempo restante de vigencia del token. El middleware de autenticación debe rechazar cualquier token que esté en la lista de revocación.

Este mecanismo ya está descrito en el Capítulo V (5.6.2) como parte del diseño.

---

## ⚠️ Decisión humana requerida ANTES de ejecutar

La implementación requiere un almacén para los tokens revocados, y hay dos caminos con trade-offs distintos. **No elijas por tu cuenta: presenta estas opciones al responsable del proyecto (Jairo) y espera su decisión.**

**Opción A — Redis (u otro almacén clave-valor con expiración automática):**
- Pros: expiración (TTL) automática nativa, muy rápido, es la solución estándar para esto, mantiene el servidor efectivamente stateless (el estado vive en un servicio externo compartido por todas las instancias).
- Contras: agrega una **nueva pieza de infraestructura** al despliegue (un servicio Redis en Railway), con su costo y configuración asociados. Hoy el proyecto **no** usa Redis.

**Opción B — Tabla en PostgreSQL:**
- Pros: no agrega infraestructura nueva (ya se usa PostgreSQL); encaja con la capa de repositorios del TICKET-02.
- Contras: no hay expiración automática (requiere un proceso/tarea periódica que borre los `jti` ya expirados, o limpiar en cada consulta); una consulta a BD por cada request autenticado añade algo de latencia.

**Prerrequisito técnico común a ambas opciones:** los tokens JWT deben incluir un identificador único `jti` en su payload. Verifica en `backend/app/core/security.py` si `create_access_token` ya incluye un `jti`. Si no lo incluye, **añadirlo es parte de este ticket** (y es un cambio de contrato del token: los tokens viejos sin `jti` seguirán siendo válidos hasta expirar, pero no podrán revocarse; acláralo en el reporte).

---

## Qué hacer (una vez elegida la opción)

1. Asegura que `create_access_token` incluya un `jti` único (por ejemplo, un UUID) y un `exp` (probablemente ya existe). Si añades `jti`, hazlo sin cambiar el resto del payload ni el algoritmo de firma (HS256).
2. Implementa el almacén de revocación según la opción elegida:
   - **Opción A:** módulo de acceso a Redis con `set(jti, ttl=<segundos restantes hasta exp>)` y `exists(jti)`.
   - **Opción B:** tabla `tokens_revocados` (`jti`, `fecha_expiracion`), su modelo ORM, su migración de Alembic, y un `RepositorioTokensRevocados` en la capa de repositorios (coherente con el TICKET-02). Incluye la limpieza de expirados.
3. En el endpoint `logout`, registra el `jti` del token actual como revocado, con expiración = tiempo restante del token.
4. En el punto donde se valida el token (probablemente `app/api/deps.py`, al decodificar el JWT y resolver el usuario), añade la comprobación: si el `jti` está revocado, rechaza con 401.
5. Documenta en el reporte cualquier variable de entorno nueva (p. ej. `REDIS_URL`) y agrégala al archivo de ejemplo de configuración con un valor de marcador, nunca real.

## Criterios de aceptación

- Tras hacer `POST /api/auth/logout` con un token, ese mismo token es rechazado con 401 en cualquier endpoint protegido posterior.
- Un token que **no** ha pasado por logout sigue funcionando normalmente hasta su expiración.
- El registro de revocación expira solo (Opción A) o se limpia mediante el mecanismo definido (Opción B), de modo que la lista no crece indefinidamente.
- Se respeta el principio stateless en la medida de lo posible (el estado de revocación vive en un almacén compartido, no en la memoria de una instancia concreta). **No** uses un set/dict en memoria del proceso como solución, porque rompería con múltiples instancias y se perdería al reiniciar.
- La suite de pruebas sigue en verde, y se agrega al menos una prueba que verifique: (a) token revocado → 401, (b) token no revocado → sigue funcionando.

## Fuera de alcance

- No cambies el tiempo de expiración del token (24 h) ni el algoritmo de firma.
- No implementes refresh tokens (sería otro ticket).
- No implementes la comprobación de revocación en memoria como atajo (ver criterios).
