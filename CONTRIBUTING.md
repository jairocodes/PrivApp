# Guía de contribución — PrivApp

## Flujo de ramas (Git Flow)

```
main           ← Versión estable, solo para entregas
  └── develop  ← Integración continua
        ├── feature/nombre-funcionalidad
        └── fix/nombre-correccion
```

### Reglas

- Nunca hacer commits directamente a `main` ni a `develop`.
- Cada cambio se trabaja en su propia rama creada desde `develop`:
  - `feature/<nombre>` para funcionalidades nuevas.
  - `fix/<nombre>` para correcciones.
  - Los cambios que solo tocan pruebas, documentación, refactorización o mantenimiento
    pueden usar el prefijo de su tipo (`test/`, `docs/`, `refactor/`, `chore/`).
- El nombre de la rama describe el cambio en español, en minúsculas y con guiones
  (por ejemplo, `feature/filtro-hallazgos`, `fix/limite-carga-temprano`). **No incluye
  números de ticket.**
- Al terminar, la rama se integra a `develop` con un merge sin avance rápido, para conservar
  el historial de la funcionalidad:

  ```bash
  git checkout develop
  git merge --no-ff feature/nombre-funcionalidad
  ```

- `main` solo recibe `develop` cuando se prepara una entrega.
- Solo se sube (`git push`) al repositorio remoto con la aprobación del responsable.

## Convención de commits

- **Commits pequeños**, uno por funcionalidad o corrección coherente: si un cambio toca el
  backend y el frontend, se puede separar en un commit por capa.
- Mensajes **en español**, en minúsculas y en tiempo presente, que describan qué cambia.
- **Sin números de ticket** en el mensaje.

Formato: `<tipo>: <descripción corta>`

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de un error |
| `test` | Adición o modificación de pruebas |
| `docs` | Cambios en documentación |
| `refactor` | Refactorización sin cambio funcional |
| `perf` | Mejoras de rendimiento |
| `chore` | Mantenimiento, configuración, dependencias |

### Ejemplos

```
feat: filtrar los hallazgos de los resultados por nivel y jurisdicción
fix: quitar los datos personales de los registros del servidor
test: ampliar la espera del análisis en segundo plano en las pruebas
docs: corregir la lista de tablas en init.sql
refactor: compartir la validación de fortaleza de contraseña
perf: búsqueda exacta en el corpus normativo
chore: actualizar versiones de dependencias del backend
```

## Pruebas obligatorias

Antes de integrar una rama a `develop`, **todas las pruebas deben pasar**:

```bash
# Backend (pytest)
docker compose exec backend pytest

# Frontend (Vitest)
docker compose exec frontend npx vitest run
```

- Toda funcionalidad o corrección nueva incluye sus pruebas.
- Las pruebas del backend usan SQLite. Las de `tests/integracion/` se ejecutan contra
  PostgreSQL con la variable `PRIVAPP_TEST_PG_URL` y **vacían las tablas**: nunca deben
  apuntar a una base de datos real.
- En Docker Desktop con WSL2, si una prueba de sesiones falla de forma aislada, repetir la
  suite antes de buscar un error (el reloj del contenedor puede desfasarse).

## Secretos y archivos de entorno

- **Nunca subir el archivo `.env`** ni ningún otro archivo con credenciales; `.env` está en
  `.gitignore`.
- No escribir claves, contraseñas ni API keys en el código, las pruebas, los commits o la
  documentación. Los valores de ejemplo van solo en `.env.example`.
- Si una variable nueva es necesaria, agregarla a `.env.example` con un valor de ejemplo y
  documentarla.

## Estándares de código

### Backend (Python)
- Estilo: PEP 8 — formatear con `black` e `isort` antes de cada commit.
- Type hints obligatorios en funciones públicas.
- Docstrings en formato Google Style.
- Nunca usar `except Exception` sin re-lanzar o registrar.
- Los registros del servidor no deben incluir datos personales (correos, nombres de
  archivos cargados, direcciones IP).

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
