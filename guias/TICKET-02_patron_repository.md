# TICKET-02 — Introducir el patrón Repository entre servicios y persistencia

**Prioridad:** Media
**Complejidad:** Media (es el ticket más grande del paquete)
**Área:** Backend — capa de servicios y acceso a datos
**Requiere decisión humana:** No (pero ver la nota sobre alcance incremental)
**Dependencias:** Ninguna, pero debe hacerse **antes** del TICKET-03.

---

## Situación actual

No existe una capa de repositorios formal. Las consultas SQLAlchemy (selects, inserts, updates) viven directamente dentro de los archivos de servicio:

- `backend/app/services/auth_service.py` — consultas sobre `User`.
- `backend/app/services/analisis_service.py` — consultas sobre `AnalysisTemp` (crear, buscar por id, actualizar progreso, guardar resultado, listar historial).
- `backend/app/services/rag_service.py` — consulta de similitud vectorial sobre `CorpusChunk` (`ORDER BY embedding <=> :vector LIMIT k`).

Los servicios importan y usan directamente `AsyncSession` y los modelos ORM para leer/escribir.

## Objetivo

Introducir una capa de repositorios dedicada (un repositorio por entidad) que encapsule todo el acceso a datos, de modo que los servicios dejen de construir consultas directamente y en su lugar llamen a métodos de repositorio con nombres de dominio. Esto aísla la lógica de negocio de los detalles de persistencia.

Este diseño ya está reflejado en los diagramas del Capítulo V (clases, secuencia y componentes muestran una "Capa de repositorios" y repositorios como `RepositorioUsuarios`, `RepositorioAnalisis`, `RepositorioCorpusNormativo`).

## Qué hacer

1. Crea un módulo nuevo: `backend/app/repositories/`.
2. Crea una clase de repositorio por entidad. Cada clase recibe la sesión (`AsyncSession`) por constructor o por parámetro de método, según el estilo que ya use el proyecto para pasar la sesión (respeta el patrón de inyección de dependencias de FastAPI ya existente en `app/api/deps.py`; **no** introduzcas un mecanismo de inyección nuevo):

   - **`RepositorioUsuarios`** (`repositories/usuarios.py`):
     - `buscar_por_correo(correo: str) -> User | None`
     - `buscar_por_id(id: int) -> User | None`
     - `crear(nombre: str, correo: str, contraseña_cifrada: str) -> User`
     - (agrega solo los métodos que `auth_service.py` realmente necesita hoy; no inventes métodos que nadie llama)

   - **`RepositorioAnalisis`** (`repositories/analisis.py`):
     - `crear(...) -> AnalysisTemp`
     - `buscar_por_id(id: int) -> AnalysisTemp | None`
     - `actualizar_progreso(id: int, seccion_actual: int) -> None`
     - `guardar_resultado(id: int, resultado: dict, estado: str) -> None`
     - `listar_por_usuario(user_id: int, page: int, page_size: int) -> ...` (respeta la forma de paginación ya usada en el endpoint de historial)
     - `marcar_error(id: int) -> None` (para el manejo de fallo total de la tarea de fondo)

   - **`RepositorioCorpusNormativo`** (`repositories/corpus.py`):
     - `buscar_similares(vector: list[float], k: int = 5, filtro_jurisdiccion: str | None = None, filtro_categoria: str | None = None) -> list[CorpusChunk]`
     - (esto absorbe la consulta vectorial que hoy está en `rag_service.py`)

3. Mueve las consultas SQLAlchemy desde los servicios hacia los métodos de repositorio correspondientes. La lógica de negocio (validaciones, orquestación, construcción de prompts, cálculo de resumen, etc.) **se queda en los servicios**; solo se mueve el acceso a datos.
4. Actualiza los servicios para que reciban/usen el repositorio correspondiente en lugar de tocar `AsyncSession`/modelos directamente para leer o escribir. Los servicios deberían dejar de importar los modelos ORM salvo para tipado.
5. Mantén el comportamiento transaccional actual. Presta especial atención al caso de `analisis_service.py` donde la tarea en segundo plano usa una **sesión de base de datos independiente** de la del request HTTP original, y al manejo de error que hace `rollback()` + marca `estado = "error"` en una transacción separada. Ese comportamiento debe preservarse exactamente; los repositorios operan sobre la sesión que se les pase, sea la del request o la de la tarea de fondo.

## Alcance incremental (recomendado)

Este ticket es grande. Se permite (y se recomienda) ejecutarlo en sub-pasos verificables, en este orden, corriendo las pruebas entre cada uno:

1. `RepositorioCorpusNormativo` (el más aislado: solo lo usa `rag_service.py`).
2. `RepositorioAnalisis` (el de mayor volumen de operaciones).
3. `RepositorioUsuarios` (el más pequeño).

Reporta cada sub-paso, pero cuéntalo como un solo ticket completado al final.

## Decisión de diseño ya tomada (no la reabras)

- **No** se requiere una interfaz abstracta base (`RepositorioBase`) ni soporte multi-motor. El proyecto usa un único motor (PostgreSQL); clases concretas por entidad son suficientes. No añadas abstracción especulativa.

## Criterios de aceptación

- Existe `backend/app/repositories/` con los tres repositorios.
- Ningún archivo en `backend/app/services/` construye consultas SQLAlchemy directamente sobre los modelos (los `select(...)`, `db.add(...)`, `db.execute(...)` de acceso a datos viven ahora en los repositorios). Excepción admisible: gestión de transacciones (`commit`/`rollback`) puede seguir coordinándose desde el servicio si ese es el patrón actual; documenta en el reporte cómo quedó repartida esa responsabilidad.
- El comportamiento externo del sistema no cambia: mismos endpoints, mismas respuestas, mismo comportamiento de la tarea en segundo plano y del manejo de errores.
- La suite de pruebas completa sigue en verde **sin modificar las pruebas existentes** (si alguna prueba accedía directamente a la lógica de acceso a datos de un servicio y se rompe, repórtalo y **pregunta** antes de tocarla — podría indicar que la prueba probaba un detalle de implementación).

## Fuera de alcance

- No cambies el esquema de la base de datos ni las migraciones.
- No cambies la firma pública de los endpoints ni de los DTOs.
- No optimices las consultas (eso sería otro ticket); haz una migración fiel, misma consulta, nuevo lugar.
