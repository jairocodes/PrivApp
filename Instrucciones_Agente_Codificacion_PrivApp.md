# Instrucciones para agente de codificación — Continuación del desarrollo de PrivApp

> Este documento es para un agente de codificación (Claude Code u otro) con acceso directo al repositorio real de PrivApp. Su propósito es retomar el desarrollo exactamente donde quedó, basándose en el análisis académico ya formalizado en el Capítulo IV del Proyecto de Graduación. No es documentación académica — es una instrucción técnica de trabajo.

---

## 1. Contexto del sistema (ya implementado, no modificar salvo indicación explícita)

PrivApp es un sistema de análisis automatizado de políticas de privacidad mediante una arquitectura de Generación Aumentada por Recuperación (RAG). Los siguientes módulos **ya están implementados y probados** (65 pruebas automatizadas verificadas con pytest):

1. **Autenticación** — registro, login, logout, consulta de perfil, protección de rutas mediante JWT, hash de contraseñas con bcrypt.
2. **Ingesta de políticas** — texto directo o extracción desde dirección web (BeautifulSoup4), validación de longitud (200–200,000 caracteres), limpieza/normalización.
3. **Motor de análisis** — segmentación de la política en secciones, recuperación de contexto normativo vía pgvector (índice ivfflat, distancia coseno), comunicación con el modelo de lenguaje mediante un adaptador de proveedor, cálculo de resumen y puntuación 0–100, generación de recomendaciones.
4. **Visualización de resultados** — panel con indicador de riesgo tipo semáforo, desglose por sección, citas normativas, recomendaciones, diseño con prioridad hacia dispositivos móviles.

**Proveedor de modelo de lenguaje documentado y a mantener como implementación de referencia: OpenAI, modelo GPT-4o-mini.** El sistema debe seguir comunicándose con este proveedor a través del adaptador ya existente (no hardcodear llamadas directas); si el adaptador ya soporta un proveedor alternativo (Gemini) internamente, no es necesario removerlo, pero **no debe presentarse ni documentarse como el proveedor activo**.

**Stack:** Python 3.11 / FastAPI (servidor asíncrono), PostgreSQL 16 + pgvector, Sentence Transformers (`paraphrase-multilingual-mpnet-base-v2`, CPU), React 18 + TypeScript + Vite + Tailwind CSS (cliente), Docker Compose (orquestación), Alembic (migraciones), pytest/vitest (pruebas).

**No modificar sin necesidad explícita:** la arquitectura de los 4 módulos existentes, el esquema de base de datos ya migrado, el adaptador de proveedor de modelo de lenguaje, ni las pruebas ya existentes (`test_auth.py`, `test_ingesta.py`, `test_analisis.py`, `test_rag.py`) — salvo que una tarea de esta lista lo requiera puntualmente.

---

## 2. Brecha identificada #1 — Falta implementar dentro del motor de análisis existente

### HU-13 — Vista de progreso con consejos de privacidad

**Historia de usuario:** Como usuario, quiero ver una vista de progreso mientras se realiza el análisis, que me muestre consejos básicos de privacidad en internet, para aprovechar el tiempo de espera de forma educativa mientras el sistema procesa mi solicitud.

**Estado actual:** no implementada. El motor de análisis ya existe y ya segmenta/procesa la política, pero no expone ningún mecanismo de progreso intermedio ni contenido educativo durante ese proceso.

**Criterios de aceptación:**
```
Dado que un usuario ha iniciado un análisis
Cuando el análisis se encuentra en proceso
Entonces el sistema mostrará una vista de progreso indicando que el análisis está en curso
Y presentará al usuario consejos básicos de privacidad en internet mientras espera

Dado que el análisis finaliza
Cuando el sistema detecta que el proceso ha concluido
Entonces reemplazará la vista de progreso por los resultados del análisis
```

**Tareas técnicas sugeridas:**
- Definir un mecanismo de progreso (opciones: *polling* periódico desde el cliente a un endpoint de estado del análisis; *server-sent events*; o *websocket*, según lo que mejor encaje con la arquitectura asíncrona ya existente del servidor). Dado que el análisis ya es un proceso por secciones (ver EP-05), el estado de progreso puede derivarse de "sección actual / total de secciones".
- Crear un pequeño repositorio de consejos de privacidad (puede ser un arreglo estático en el servidor o un archivo de configuración; no requiere corpus vectorial ni modelo de lenguaje — son tips genéricos, no generados dinámicamente).
- En el cliente, construir el componente de vista de progreso (React) que consuma el estado y muestre un consejo (rotando entre varios) mientras el análisis está en curso, y transicione automáticamente a la vista de resultados al finalizar.
- Regla de negocio a respetar: esta vista no debe alterar el tiempo total de procesamiento del análisis ni introducir esperas artificiales — es solo una capa de retroalimentación visual sobre un proceso que ya ocurre.

**Requerimiento no funcional relacionado (RU-03 y RU-04, sección 4.5.3):** el indicador debe seguir el mismo lenguaje visual sencillo (sin tecnicismos) ya usado en el resto del panel de resultados.

---

## 3. Brecha identificada #2 — Módulo 5 completo (no implementado)

### EP-07 — Repositorio y generación de reportes

Este módulo es nuevo por completo; ningún componente de esta épica existe todavía en el repositorio.

#### HU-14 — Historial de análisis

**Historia de usuario:** Como usuario, quiero consultar un historial con todos mis análisis anteriores, para revisarlos sin tener que recordar cada identificador.

**Criterios de aceptación:**
```
Dado que un usuario autenticado ha generado análisis previamente
Cuando solicita ver su historial
Entonces el sistema mostrará una lista de sus análisis anteriores
Y cada elemento de la lista permitirá acceder al detalle correspondiente

Dado que un usuario no ha generado ningún análisis previo
Cuando solicita ver su historial
Entonces el sistema mostrará una indicación de que aún no cuenta con análisis registrados
```

**Tareas técnicas sugeridas:**
- Nuevo endpoint de servidor: listado paginado de análisis pertenecientes al usuario autenticado (reutilizar el mecanismo de verificación de pertenencia ya usado en el endpoint de consulta de análisis individual, HU-12).
- Nuevo componente de cliente: vista de historial (lista o tabla) con navegación al detalle de cada análisis ya existente.
- Considerar orden por fecha descendente (más reciente primero) como criterio por defecto.

#### HU-15 — Descarga de reporte en PDF

**Historia de usuario:** Como usuario, quiero descargar un reporte en formato PDF de un análisis realizado, para conservar o compartir los resultados fuera del sistema.

**Criterios de aceptación:**
```
Dado que un usuario cuenta con un análisis finalizado
Cuando solicita descargar el reporte correspondiente
Entonces el sistema generará un documento en formato PDF con el resumen, los hallazgos y las citas normativas del análisis
Y permitirá al usuario descargarlo o conservarlo fuera del sistema
```

**Tecnología designada (ya decidida, no elegir otra):** ReportLab 4.2.5, generación de PDF en memoria (sin escribir archivos temporales a disco, consistente con el resto de la arquitectura *stateless* del servidor).

**Tareas técnicas sugeridas:**
- Nuevo endpoint de servidor que reciba el identificador del análisis, verifique pertenencia al usuario (mismo patrón que HU-12/HU-14), y genere el PDF en memoria a partir de los datos ya persistidos del análisis (resumen, hallazgos por sección, citas normativas, recomendaciones).
- Definir una plantilla de reporte simple: encabezado con nombre del sistema y fecha, resumen ejecutivo con puntuación e indicador de riesgo, secciones con hallazgos y su cita normativa, listado de recomendaciones.
- Respuesta HTTP con el tipo de contenido correspondiente a PDF, para que el cliente lo descargue directamente sin pasos intermedios.
- En el cliente, agregar el botón/acción de descarga tanto en la vista de resultados de un análisis nuevo como en el detalle de un análisis consultado desde el historial (HU-14).

**Reglas de negocio aplicables a todo el módulo:**
- Todo hallazgo mostrado en el reporte debe seguir respaldado por al menos una fuente normativa citada (misma regla ya aplicada en el motor de análisis).
- El sistema debe distinguir normativa de Guatemala vs. internacional también dentro del PDF generado, no solo en el panel web.

---

## 4. Requerimientos no funcionales a verificar/aplicar sobre las nuevas funcionalidades

Estos ya están definidos para el sistema en general (Capítulo IV, sección 4.5); aplican también a lo nuevo de este módulo:

| Código | Requerimiento | Aplicación a este módulo |
|---|---|---|
| RS-03 | Limitación de tasa de solicitudes | Evaluar si el endpoint de generación de PDF necesita su propio límite de tasa, dado que generar un PDF tiene un costo de cómputo distinto al de una simple consulta. |
| RS-07 | Validación de entrada en los límites del sistema | El endpoint de historial debe validar parámetros de paginación (límites razonables de página/tamaño). |
| RR-01 | Arquitectura asíncrona sin bloqueos | La generación del PDF con ReportLab debe evaluarse para no bloquear el bucle de eventos asíncrono del servidor (considerar ejecutarla en un hilo/proceso auxiliar si ReportLab no es nativamente asíncrono). |
| RE-01 | Servidor sin estado de sesión propio | El nuevo endpoint de reportes debe seguir el mismo patrón *stateless* basado en el token de acceso, sin introducir sesión en servidor. |
| RC-04 | Reproducibilidad vía contenedores | Si ReportLab requiere alguna dependencia adicional del sistema operativo, debe agregarse a la imagen de contenedor del servidor, no asumirse como preinstalada. |

---

## 5. Pruebas automatizadas a construir

Siguiendo el mismo patrón ya establecido en el repositorio (una suite por módulo):

- **`test_progreso.py`** (o incorporarlo a `test_analisis.py` si el equipo lo prefiere así): pruebas del estado de progreso durante un análisis en curso, y de la transición a resultados al finalizar.
- **`test_reportes.py`**: pruebas del endpoint de historial (listado, paginación, historial vacío, aislamiento entre usuarios) y del endpoint de generación de PDF (generación exitosa, verificación de pertenencia, contenido mínimo esperado en el documento generado).

Mantener el mismo criterio ya usado en el resto del proyecto: entorno de pruebas desacoplado de servicios externos (sin necesidad de generar PDFs reales masivos ni depender del proveedor del modelo de lenguaje para probar historial/reportes, ya que estos módulos no invocan al modelo de lenguaje directamente).

---

## 6. Fuera de alcance — no implementar en este ciclo

- **Extensión de navegador (Chrome u otro):** decisión ya tomada de excluirla del alcance actual del proyecto. No iniciar ningún trabajo relacionado; queda documentada únicamente como recomendación de trabajo futuro en las conclusiones del proyecto de graduación.
- **Migración o soporte adicional de proveedores de modelo de lenguaje** más allá de lo que el adaptador ya soporta.
- **Cambio de plataforma de despliegue:** aún en evaluación por el estudiante (Railway vs. alternativas); no depende de este ciclo de desarrollo.

---

## 7. Al finalizar este ciclo

- Actualizar el conteo real de pruebas automatizadas (documentar el nuevo total, ya que el Capítulo IV cita la cifra de 65 como dato verificado y deberá actualizarse si se agregan pruebas nuevas).
- Actualizar la documentación técnica y el manual del evaluador (EP-08) para reflejar el Módulo 5 y la vista de progreso como funcionalidades entregadas.
- Confirmar si es necesario actualizar el archivo `.env`/variables de entorno con alguna configuración nueva (por ejemplo, parámetros de la vista de progreso o de generación de PDF).
