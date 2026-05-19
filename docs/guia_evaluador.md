# Guía del Evaluador — PrivApp v1.0-prototipo

**Documento para:** Asesora Sheyla Esquivel y evaluadores del Proyecto de Graduación I  
**Autor:** Jairo Ardani Castillo Girón — castillo.jairo99930@gmail.com  
**Carné:** 0905-22-12005 | UMG Campus Jutiapa  
**Versión:** 1.0-prototipo (todos los sprints completados)

---

## ¿Qué hace el sistema?

PrivApp analiza automáticamente políticas de privacidad de servicios digitales y presenta
los resultados en lenguaje claro para jóvenes de San José Acatempa, Jutiapa.

El flujo completo es:

1. **El usuario se registra e inicia sesión.**
2. **Ingresa la política** pegando el texto o indicando la URL de la página.
3. **El sistema segmenta** la política en secciones temáticas (máximo 8).
4. **Para cada sección**, busca en el corpus normativo los fragmentos legales más
   relevantes (top-5 por similitud semántica con pgvector).
5. **Envía a Gemini** un prompt enriquecido: la sección + el contexto normativo +
   el system prompt que define los criterios de riesgo OPP-115.
6. **Valida la respuesta JSON** del LLM; si está malformada, solicita corrección automática.
7. **Presenta el análisis** con semáforo de riesgo, secciones expandibles, hallazgos
   con citas a fuentes normativas (con distinción Guatemala vs Internacional) y
   recomendaciones accionables.

---

## Módulos implementados en el prototipo

| Módulo | Estado | Sprint |
|---|---|---|
| Infraestructura Docker (backend + frontend + PostgreSQL) | Completado | Sprint 0 |
| Autenticación JWT (registro, login, logout, perfil) | Completado | Sprint 1 |
| Corpus normativo + arquitectura RAG (pgvector + Sentence Transformers) | Completado | Sprint 2 |
| Ingesta de políticas (texto directo y extracción desde URL) | Completado | Sprint 3 |
| Motor de Análisis (segmentación + RAG + Gemini + validación JSON) | Completado | Sprint 4 |
| Panel de Visualización mobile-first (semáforo, secciones, citas, recomendaciones) | Completado | Sprint 5 |

**Módulos excluidos del prototipo** (Proyecto de Graduación II):
- Repositorio histórico de análisis del usuario
- Generación de reportes descargables en PDF

---

## Requisitos para ejecutar el sistema

1. **Docker Desktop** instalado y en ejecución.
2. Archivo `.env` configurado (ver `docs/instalacion.md`).
3. **API key de Google Gemini** en la variable `GEMINI_API_KEY` del `.env`.
4. PDFs del corpus normativo colocados en `corpus_normativo/` (ver `corpus_normativo/README.md`).

---

## Cómo probar el sistema — paso a paso

### Paso 1: Levantar el sistema

```bash
docker compose up --build
```

Esperar hasta ver en los logs:
```
backend  | INFO: Application startup complete.
frontend | Local: http://localhost:5173/
```

### Paso 2: Preparar la base de datos

```bash
# En otra terminal:
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/cargar_corpus.py
```

### Paso 3: Verificar servicios

| URL | Resultado esperado |
|---|---|
| http://localhost:5173 | Pantalla de inicio de sesión de PrivApp |
| http://localhost:8000/health | `{"status": "ok", "version": "0.4.0"}` |
| http://localhost:8000/docs | Swagger UI con todos los endpoints |

---

## Casos de prueba del prototipo

### CP-01: Registro de usuario nuevo

1. Abrir http://localhost:5173
2. Hacer clic en "Crear cuenta".
3. Completar: nombre, correo electrónico, contraseña (mínimo 8 caracteres, una mayúscula, un número).
4. **Resultado esperado:** El sistema inicia sesión automáticamente y muestra el Dashboard.

### CP-02: Inicio de sesión

1. Cerrar sesión (botón en la barra de navegación).
2. Iniciar sesión con las credenciales registradas.
3. **Resultado esperado:** Acceso al Dashboard con saludo personalizado.

### CP-03: Análisis de política por texto (caso principal)

1. Desde el Dashboard, hacer clic en "Analizar política".
2. En la pestaña "Pegar texto", copiar el siguiente fragmento de una política real
   (o usar el texto de ejemplo al final de este documento).
3. Hacer clic en "Analizar política".
4. Esperar 10-30 segundos (el sistema procesa con Gemini).
5. **Resultado esperado:**
   - Pantalla de resultados con resumen ejecutivo (semáforo + puntaje).
   - Al menos 2 secciones analizadas.
   - Hallazgos con nivel de riesgo (bajo/medio/alto).
   - Al menos una cita normativa con badge de jurisdicción.
   - Lista de recomendaciones.

### CP-04: Análisis de política por URL

1. Desde "Analizar política", seleccionar la pestaña "Desde URL".
2. Ingresar la URL de una política de privacidad pública (ej. la de un servicio conocido).
3. **Resultado esperado:** El sistema extrae el texto y produce el análisis.
4. **Si la URL falla** (sitio con JavaScript dinámico): el sistema muestra un mensaje
   de error claro y el usuario puede cambiar a la pestaña de texto.

### CP-05: Validación de rutas protegidas

1. Copiar la URL http://localhost:5173/analizar
2. Cerrar sesión.
3. Intentar acceder a la URL copiada.
4. **Resultado esperado:** Redirección automática a `/login`.

### CP-06: Distinción de jurisdicción en citas

1. En los resultados de un análisis, expandir una sección con hallazgos.
2. **Resultado esperado:**
   - Citas de normativa guatemalteca (Constitución, LAIP) con badge **azul "Guatemala"**.
   - Citas de RGPD, Principios OEA, etc. con badge **morado "Internacional"** y nota
     aclaratoria: *"Referencia internacional — buena práctica, no ley vigente en Guatemala."*

### CP-07: Visualización mobile

1. Abrir las herramientas de desarrollador del navegador (F12).
2. Activar la vista de dispositivo móvil (375px de ancho).
3. Navegar por la pantalla de resultados.
4. **Resultado esperado:** La interfaz es usable: texto legible (≥16px), botones accesibles,
   secciones expandibles funcionan correctamente.

---

## Texto de ejemplo para pruebas (CP-03)

```
POLÍTICA DE PRIVACIDAD — EJEMPLO DE PRUEBA

1. DATOS QUE RECOPILAMOS
Recopilamos información personal que nos proporcionas al crear una cuenta, como tu nombre,
dirección de correo electrónico, número de teléfono y fecha de nacimiento. También
recopilamos automáticamente datos de uso, incluyendo las páginas que visitas, el tiempo
que pasas en ellas, tu dirección IP y el tipo de dispositivo y navegador que utilizas.
Podemos recopilar información de ubicación precisa si nos otorgas permiso.

2. CÓMO USAMOS TUS DATOS
Utilizamos la información recopilada para proporcionar y mejorar nuestros servicios,
personalizar tu experiencia y mostrarte publicidad relevante. Podemos compartir tus datos
con socios comerciales, anunciantes y otros terceros para fines de marketing. También
podemos vender datos agregados y anonimizados a terceros. Tus datos podrán ser transferidos
a servidores ubicados fuera de tu país de residencia, donde las leyes de protección de
datos pueden ser distintas.

3. CONSERVACIÓN DE DATOS
Conservamos tus datos mientras mantengas una cuenta activa con nosotros o según sea
necesario para prestarte servicios. No establecemos un plazo máximo de conservación.
Podemos conservar cierta información incluso después de que elimines tu cuenta por razones
legales o comerciales.

4. TUS DERECHOS
Puedes acceder, corregir o eliminar tus datos personales contactándonos por correo
electrónico. El proceso puede tardar hasta 30 días hábiles. Algunos datos no pueden
eliminarse por razones técnicas o legales.

5. CAMBIOS A ESTA POLÍTICA
Nos reservamos el derecho de modificar esta política en cualquier momento. Te notificaremos
por correo electrónico si realizamos cambios materiales, pero el uso continuado del servicio
después de la publicación de los cambios constituirá tu aceptación.
```

---

## Preguntas frecuentes para el evaluador

**¿El análisis siempre cita fuentes reales?**  
Sí. El sistema usa RAG: cada sección se analiza junto a los fragmentos normativos reales
del corpus (RGPD, Principios OEA, Constitución de Guatemala, LAIP, OPP-115) más relevantes
por similitud semántica. Gemini tiene instrucción explícita de no inventar referencias.

**¿Qué pasa si Gemini falla o devuelve JSON inválido?**  
El sistema reintenta automáticamente hasta 3 veces (backoff exponencial). Si la respuesta
sigue siendo inválida, esa sección muestra "No fue posible analizar esta sección" y el
análisis continúa con las demás. El resultado siempre se entrega al usuario.

**¿Los datos del usuario se almacenan permanentemente?**  
Los análisis se almacenan en la tabla `analysis_temp` mientras dure la sesión del
prototipo. No hay repositorio histórico en este prototipo (módulo excluido).

**¿Por qué se usan referencias internacionales si Guatemala no tiene ley de datos?**  
El sistema distingue explícitamente: las referencias guatemaltecas (Constitución, LAIP)
se presentan como normativa vigente; las internacionales (RGPD, OEA) se presentan como
buenas prácticas con nota aclaratoria. Esto es por diseño y está documentado en
`docs/arquitectura.md`.
