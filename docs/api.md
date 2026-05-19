# Documentación de la API — PrivApp

La documentación interactiva completa (Swagger UI) está disponible en:

```
http://localhost:8000/docs
```

ReDoc (formato alternativo):
```
http://localhost:8000/redoc
```

## Resumen de endpoints

### Sistema

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/health` | Estado del servicio | No |

### Autenticación (`/api/auth`)

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | Registro de usuario | No |
| POST | `/api/auth/login` | Inicio de sesión | No |
| POST | `/api/auth/logout` | Cierre de sesión | Sí |
| GET | `/api/auth/me` | Datos del usuario actual | Sí |

### Ingesta (`/api/ingesta`)

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/api/ingesta/texto` | Recibe texto plano de política | Sí |
| POST | `/api/ingesta/url` | Extrae texto desde URL | Sí |

### Análisis (`/api/analisis`)

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/api/analisis/iniciar` | Inicia análisis de una política | Sí |
| GET | `/api/analisis/{id}` | Obtiene resultados de un análisis | Sí |

## Autenticación

Todos los endpoints protegidos requieren el header:

```
Authorization: Bearer <token_jwt>
```

El token se obtiene en la respuesta de `/api/auth/login` o `/api/auth/register`.

## Formato de errores

```json
{
  "detail": "Mensaje descriptivo del error."
}
```

## Estado de implementación

| Endpoints | Estado |
|---|---|
| `/health` | Implementado (Sprint 0) |
| `/api/auth/*` | Sprint 1 |
| `/api/ingesta/*` | Sprint 3 |
| `/api/analisis/*` | Sprint 4 |
