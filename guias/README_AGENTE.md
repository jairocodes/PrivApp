# Paquete de mejoras para PrivApp — Instrucciones para el agente ejecutor

Este paquete contiene un conjunto de tareas de mejora acotadas para el sistema PrivApp. Cada tarea vive en su propio archivo `TICKET-XX_*.md` y está pensada para ejecutarse de forma independiente. Este README define **cómo** debes trabajar. Léelo completo antes de tocar cualquier archivo del repositorio.

---

## Contexto mínimo del proyecto

- **Servidor:** FastAPI (Python), estructura en `backend/app/`, arquitectura en capas (`api/` → `services/` → `models/` + `database.py`, con `schemas/` como capa de contratos y `core/`/`utils/` como utilidades compartidas).
- **Cliente:** React 18 + TypeScript + Vite + Tailwind CSS, en `frontend/`.
- **Base de datos:** PostgreSQL 16 con extensión `pgvector`.
- **Proveedor de modelo de lenguaje:** OpenAI (`gpt-4o-mini`) como adaptador activo; existe un adaptador Gemini alterno.
- **Pruebas:** el proyecto cuenta con una suite de pruebas automatizadas (referida como ~65 pruebas). Son tu red de seguridad principal.
- **Despliegue:** Railway.

> Las rutas de archivo en los tickets se dan desde la raíz del repositorio (p. ej. `backend/app/services/llm/openai_adapter.py`). Si la estructura real difiere, **detente y reporta** (ver Regla 2), no adivines la ruta equivalente.

---

## Reglas de trabajo (obligatorias)

**Regla 1 — Alcance estrictamente limitado.**
Modifica **únicamente** lo que el ticket indica. No refactorices código aledaño, no renombres variables no relacionadas, no reformatees archivos completos, no actualices dependencias, no "aproveches para" mejorar otras cosas. Si ves algo más que valdría la pena mejorar, anótalo en la sección "Observaciones fuera de alcance" de tu reporte del ticket, pero **no lo toques**.

**Regla 2 — Verificar antes de asumir.**
Antes de editar, confirma que el archivo, la función y el contexto descritos en el ticket existen tal como se describen. Las referencias a números de línea son aproximadas (`~339`) y pueden haberse desplazado; úsalas como orientación, no como verdad absoluta: localiza el código por su nombre de función/símbolo, no por la línea. Si el archivo o la función no existe, o el código actual ya no coincide con la "Situación actual" descrita en el ticket, **detente y reporta la discrepancia** en vez de improvisar.

**Regla 3 — Las pruebas mandan.**
1. Antes de empezar cada ticket, ejecuta la suite de pruebas y confirma que está en verde. Si ya hay pruebas rojas antes de tu cambio, repórtalo y no continúes (no quieres que te atribuyan un fallo preexistente).
2. Después de tu cambio, ejecuta de nuevo la suite completa. Todas las pruebas que pasaban antes deben seguir pasando.
3. Si el ticket pide una prueba nueva, agrégala y confírmala en verde.
4. Nunca modifiques una prueba existente para "hacerla pasar" a menos que el ticket lo pida explícitamente y justifiques por qué la prueba anterior era incorrecta.

**Regla 4 — Un ticket = un cambio atómico.**
No mezcles varios tickets en un mismo conjunto de cambios. Completa, verifica y reporta un ticket antes de pasar al siguiente. Respeta el orden de dependencias indicado más abajo.

**Regla 5 — No romper el contrato externo sin avisar.**
No cambies rutas de endpoints, nombres de campos de request/response, ni la forma del JSON que consume el cliente, salvo que el ticket lo indique. Si un cambio interno obliga a un cambio de contrato, **detente y reporta** antes de proceder.

**Regla 6 — Secretos y configuración.**
Nunca escribas credenciales, llaves ni valores de `.env` en el código ni en los reportes. Si un ticket requiere una variable de entorno nueva, decláralo en el reporte y añádela al archivo de ejemplo de configuración (`.env.example` o equivalente) con un valor de marcador de posición, no un valor real.

**Regla 7 — Reporte por ticket.**
Al terminar cada ticket, entrega un reporte breve con: (a) archivos modificados, (b) resumen del cambio, (c) resultado de las pruebas antes/después, (d) cualquier discrepancia encontrada, (e) observaciones fuera de alcance. Hay una plantilla al final de este archivo.

---

## Orden de ejecución recomendado

El orden importa porque algunos tickets cambian dónde vive la lógica de acceso a datos.

| Orden | Ticket | Por qué en esta posición |
|---|---|---|
| 1 | **TICKET-01** — Conectar `_es_error_reintentable` al `@retry` | Cambio mínimo y aislado; no depende de nada. Buen primer paso para validar tu flujo de pruebas. |
| 2 | **TICKET-04** — Paleta semántica `riesgo.*` en el cliente | Aislado, solo frontend, no interfiere con el backend. |
| 3 | **TICKET-05** — Etiqueta textual en el indicador de semáforo | Aislado, solo frontend. Relacionado con el TICKET-04 (mismo componente probablemente), por eso va justo después. |
| 4 | **TICKET-06** — `--proxy-headers` en el arranque de Uvicorn | Configuración de despliegue, no toca lógica de aplicación. |
| 5 | **TICKET-02** — Introducir el patrón Repository | Refactorización estructural del backend. Va **antes** del TICKET-03 porque ese debería construirse sobre la capa de repositorios ya existente. Es el ticket más grande. |
| 6 | **TICKET-03** — Invalidación real de sesión (logout) | Depende de una decisión de infraestructura (ver el ticket) y se beneficia de que la capa de repositorios del TICKET-02 ya exista. **Requiere confirmación humana antes de ejecutarse.** |

> **TICKET-03 y TICKET-07 requieren decisión/confirmación humana.** No los ejecutes de forma autónoma sin la aprobación descrita dentro de cada uno. TICKET-07 es una verificación administrativa, no un cambio de código.

---

## Plantilla de reporte por ticket

```
## Reporte — TICKET-XX

**Estado:** Completado / Bloqueado / Requiere decisión

**Archivos modificados:**
- ruta/al/archivo.py
- ...

**Resumen del cambio:**
(2-4 líneas describiendo qué se hizo)

**Pruebas:**
- Antes: X pasando / Y fallando
- Después: X pasando / Y fallando
- Pruebas nuevas agregadas: (sí/no, cuáles)

**Discrepancias encontradas:**
(el código no coincidía con lo descrito / la ruta era distinta / etc. — o "ninguna")

**Observaciones fuera de alcance:**
(cosas que notaste pero NO tocaste, por si el humano quiere abrir otro ticket — o "ninguna")
```
