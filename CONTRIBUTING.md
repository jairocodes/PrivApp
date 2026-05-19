# Guía de contribución — PrivApp

## Flujo de ramas (Git Flow)

```
main           ← Versión estable, lista para entrega
  └── develop  ← Integración continua
        ├── feature/sprint-N-nombre-funcionalidad
        └── release/sprint-N
hotfix/nombre  ← Correcciones urgentes desde main
```

### Reglas

- Nunca hacer commits directamente a `main`.
- Las `feature/` branches se crean desde `develop`.
- Al cerrar un Sprint, se crea una rama `release/sprint-N` desde `develop`, se prueba, y se mergea a `main` y `develop`.

## Convención de commits

Formato: `<tipo>(<alcance>): <descripción corta>`

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato sin cambios de lógica |
| `refactor` | Refactorización sin cambio funcional |
| `test` | Adición o modificación de tests |
| `chore` | Mantenimiento, configuración |
| `perf` | Mejoras de rendimiento |

### Ejemplos

```
feat(auth): implementar endpoint de registro con validación bcrypt
fix(motor): corregir manejo de timeout en llamada a Gemini
docs(readme): agregar instrucciones de carga del corpus
chore(deps): actualizar versiones de dependencias del backend
test(auth): agregar test de login con credenciales inválidas
```

## Estándares de código

### Backend (Python)
- Estilo: PEP 8 — formatear con `black` e `isort` antes de cada commit.
- Type hints obligatorios en funciones públicas.
- Docstrings en formato Google Style.
- Nunca usar `except Exception` sin re-lanzar o registrar.

### Frontend (TypeScript/React)
- TypeScript estricto — evitar `any`.
- Un componente por archivo.
- PascalCase para componentes, camelCase para funciones y variables.

## Ejecutar linters

```bash
# Backend
docker compose exec backend black app/ tests/
docker compose exec backend isort app/ tests/
docker compose exec backend flake8 app/ tests/

# Frontend
cd frontend && npm run lint
```
