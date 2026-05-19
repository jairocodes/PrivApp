# Guía del Evaluador — PrivApp

**Documento para:** Asesora Sheyla Esquivel y evaluadores del Proyecto de Graduación I  
**Versión:** Prototipo 0.1.0 (Sprint 0 completado)

---

## ¿Qué hace el sistema?

PrivApp analiza automáticamente políticas de privacidad de servicios digitales.
El usuario pega el texto de una política (o su URL), y el sistema:

1. Segmenta la política en secciones temáticas.
2. Busca en un corpus de normativa legal (guatemalteca e internacional) los fragmentos relevantes para cada sección.
3. Envía las secciones junto al contexto normativo al modelo de IA Gemini.
4. Presenta los resultados con indicadores de riesgo (semáforo: rojo/amarillo/verde) y citas a las fuentes legales.

El objetivo es que jóvenes de San José Acatempa, Jutiapa, puedan entender qué hacen las aplicaciones con sus datos.

---

## Módulos implementados en este prototipo

| Módulo | Estado | Sprint |
|---|---|---|
| Infraestructura Docker | Completado | Sprint 0 |
| Autenticación (registro, login) | Pendiente | Sprint 1 |
| Ingesta de políticas (texto/URL) | Pendiente | Sprint 3 |
| Motor de Análisis (RAG + Gemini) | Pendiente | Sprint 4 |
| Panel de Visualización | Pendiente | Sprint 5 |

**Módulos excluidos del prototipo** (se implementarán en Proyecto de Graduación II):
- Repositorio histórico de análisis
- Generación de reportes descargables en PDF

---

## Cómo probar el sistema (Sprint 0)

### Prerrequisitos
1. Docker Desktop instalado.
2. Archivo `.env` configurado (ver `docs/instalacion.md`).

### Pasos de verificación

```bash
# 1. Levantar el sistema
docker compose up --build

# 2. Verificar el backend
curl http://localhost:8000/health
# Respuesta esperada: {"status": "ok", "service": "privapp-backend", ...}

# 3. Verificar el frontend
# Abrir en el navegador: http://localhost:5173
# Se debe mostrar la pantalla de login de PrivApp.

# 4. Verificar documentación de la API
# Abrir en el navegador: http://localhost:8000/docs
# Se debe mostrar Swagger UI con el endpoint /health.
```

---

## Casos de prueba planificados (disponibles en Sprint 5)

1. Registro de usuario nuevo.
2. Inicio de sesión con las credenciales registradas.
3. Ingesta de la política de privacidad de Instagram por texto.
4. Generación del análisis completo.
5. Visualización del panel con indicadores de riesgo.
6. Verificación de citas normativas (badge Guatemala vs Internacional).
7. Cierre de sesión — verificación de rutas protegidas.

---

## Contacto del desarrollador

**Jairo Ardani Castillo Girón** — castillo.jairo99930@gmail.com  
Carné: 0905-22-12005 | UMG Campus Jutiapa
