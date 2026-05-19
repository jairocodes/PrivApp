# Documentación de la API — PrivApp v1.0

La documentación interactiva completa (Swagger UI) está disponible con el sistema en ejecución:

```
http://localhost:8000/docs       ← Swagger UI (recomendada)
http://localhost:8000/redoc      ← ReDoc (formato alternativo)
```

---

## Autenticación

Todos los endpoints marcados como **Sí** en la columna Auth requieren el header:

```http
Authorization: Bearer <token_jwt>
```

El token se obtiene en la respuesta de `POST /api/auth/login` o `POST /api/auth/register`.
Expira a las **24 horas**.

---

## Endpoints

### Sistema

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| GET | `/health` | Estado del servicio y versión | No | — |

**Respuesta `/health`:**
```json
{
  "status": "ok",
  "service": "privapp-backend",
  "version": "0.4.0",
  "environment": "development"
}
```

---

### Autenticación — `/api/auth`

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/api/auth/register` | Registro de usuario nuevo | No | 10/min |
| POST | `/api/auth/login` | Inicio de sesión | No | 5/min |
| POST | `/api/auth/logout` | Cierre de sesión (client-side) | Sí | — |
| GET | `/api/auth/me` | Datos del usuario autenticado | Sí | — |

**Body `POST /register`:**
```json
{
  "nombre": "Jairo Castillo",
  "email": "jairo@ejemplo.com",
  "password": "MiClave123"
}
```
Reglas de contraseña: mínimo 8 caracteres, al menos una mayúscula y un número.

**Body `POST /login`:**
```json
{
  "email": "jairo@ejemplo.com",
  "password": "MiClave123"
}
```

**Respuesta de registro y login:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nombre": "Jairo Castillo",
    "email": "jairo@ejemplo.com"
  }
}
```

---

### Ingesta — `/api/ingesta`

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/api/ingesta/texto` | Recibe y limpia texto plano de política | Sí | 20/min |
| POST | `/api/ingesta/url` | Descarga y extrae texto desde URL | Sí | 10/min |

**Body `POST /texto`:**
```json
{
  "texto": "Texto de la política de privacidad... (mín. 200, máx. 50 000 caracteres)"
}
```

**Body `POST /url`:**
```json
{
  "url": "https://ejemplo.com/politica-de-privacidad"
}
```

**Respuesta (ambos):**
```json
{
  "texto_procesado": "Texto normalizado listo para análisis...",
  "palabras": 1250,
  "fuente": "texto_directo"
}
```

> **Nota:** Si la URL requiere JavaScript dinámico (SPA) o devuelve un error HTTP,
> el endpoint retorna HTTP 422 con un mensaje descriptivo.

---

### Análisis — `/api/analisis`

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/api/analisis/iniciar` | Inicia el análisis de una política | Sí | 5/min |
| GET | `/api/analisis/{id}` | Recupera un análisis completado | Sí | — |

**Body `POST /iniciar`:**
```json
{
  "texto": "Texto limpio de la política... (mín. 200, máx. 50 000 caracteres)"
}
```

> Este endpoint puede tardar entre 10 y 60 segundos según el número de secciones y
> la latencia de la API de Gemini.

**Respuesta `POST /iniciar` y `GET /{id}` (HTTP 201 / 200):**
```json
{
  "id_analisis": "42",
  "fecha": "2026-05-18T14:30:00Z",
  "resumen_general": {
    "nivel_riesgo_global": "medio",
    "puntaje": 55,
    "comentario_breve": "Se detectaron 3 hallazgos de riesgo medio..."
  },
  "secciones_analizadas": [
    {
      "categoria_opp115": "First Party Collection/Use",
      "titulo": "Recopilación de datos personales",
      "texto_original": "Fragmento de la política analizado...",
      "hallazgos": [
        {
          "tipo": "riesgo",
          "descripcion": "Se comparten datos con terceros no identificados.",
          "nivel": "alto",
          "fuentes_normativas": [
            {
              "documento": "Principios OEA 2021",
              "referencia": "Principio 5 — Transferencia de datos",
              "fragmento_relevante": "Toda transferencia debe contar con garantías adecuadas..."
            }
          ]
        }
      ]
    }
  ],
  "recomendaciones": [
    "En 'Recopilación de datos': Se comparten datos con terceros no identificados.",
    "Revisa detenidamente las cláusulas de transferencia antes de aceptar."
  ]
}
```

---

## Códigos de error

| HTTP | Código | Descripción |
|---|---|---|
| 401 | — | Token JWT inválido o expirado |
| 403 | — | Sin token en el header Authorization |
| 404 | — | Análisis no encontrado o no pertenece al usuario |
| 409 | — | Correo electrónico ya registrado |
| 422 | — | Datos de entrada inválidos (texto demasiado corto, URL inaccesible, etc.) |
| 429 | — | Rate limit excedido |
| 502 | — | Error de comunicación con Gemini API |

**Formato de error:**
```json
{
  "detail": "Mensaje descriptivo del error."
}
```

---

## Flujo de integración recomendado

```
1. POST /api/auth/register  →  obtener token
2. POST /api/ingesta/texto  →  obtener texto_procesado
3. POST /api/analisis/iniciar (con texto_procesado) → obtener resultado completo
4. Mostrar resultado al usuario (id_analisis para recuperación futura)
```
