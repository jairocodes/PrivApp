# Documentación de la API — PrivApp v2.0

La documentación interactiva completa (Swagger UI) está disponible con el sistema en ejecución:

```
http://localhost:8000/docs       ← Swagger UI (recomendada)
http://localhost:8000/redoc      ← ReDoc (formato alternativo)
```

---

## Autenticación

Los endpoints marcados como **Usuario** o **Administrador** en la columna Auth requieren el header:

```http
Authorization: Bearer <token_jwt>
```

- El token se obtiene en la respuesta de `POST /api/auth/register`, `POST /api/auth/login` o
  `POST /api/auth/change-password`. Expira a las **24 horas**.
- **Usuario:** cualquier cuenta activa con un token vigente.
- **Administrador:** además, la cuenta debe tener el rol `administrador`. El servidor consulta el
  rol vigente en la base de datos (no el que viaja en el token), de modo que un cambio de rol tiene
  efecto inmediato.
- Un token deja de ser válido (HTTP 401) cuando:
  - expira o su firma no es válida;
  - se cerró la sesión con `POST /api/auth/logout` (el identificador del token se revoca);
  - se cambió la contraseña o un administrador desactivó la cuenta (se invalidan todas las sesiones
    emitidas antes de ese momento);
  - la cuenta fue eliminada o está inactiva.

---

## Límites de solicitudes

Los límites se aplican por dirección IP y por minuto. Al excederlos, la API responde **HTTP 429**
con `{"detail": "Demasiadas solicitudes. Espera un minuto antes de volver a intentarlo."}`.
Las rutas sin límite se indican con "—".

| Ruta | Límite |
|---|---|
| `POST /api/auth/register` | 10/min |
| `POST /api/auth/login` | 5/min |
| `POST /api/auth/change-password` | 5/min |
| `DELETE /api/auth/me` | 5/min |
| `POST /api/ingesta/texto` | 20/min |
| `POST /api/ingesta/url` | 10/min |
| `POST /api/ingesta/archivo` | 10/min |
| `POST /api/analisis/iniciar` | 5/min |
| `GET /api/analisis/{id}/pdf` | 10/min |
| `POST /api/admin/corpus` | 5/min |

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
  "version": "2.0.0",
  "environment": "development"
}
```

---

### Autenticación — `/api/auth`

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/api/auth/register` | Registro de usuario nuevo | No | 10/min |
| POST | `/api/auth/login` | Inicio de sesión | No | 5/min |
| POST | `/api/auth/logout` | Cierre de sesión (revoca el token actual) | Usuario | — |
| GET | `/api/auth/me` | Datos del usuario autenticado | Usuario | — |
| PATCH | `/api/auth/me` | Edita el nombre del usuario autenticado | Usuario | — |
| DELETE | `/api/auth/me` | Elimina de forma definitiva la propia cuenta | Usuario | 5/min |
| POST | `/api/auth/change-password` | Cambia la contraseña | Usuario | 5/min |

#### `POST /api/auth/register` — HTTP 201

**Body:**
```json
{
  "nombre": "Jairo Castillo",
  "email": "jairo@ejemplo.com",
  "password": "MiClave123",
  "acepta_aviso": true,
  "declara_edad": true
}
```

- `nombre`: de 2 a 100 caracteres.
- `email`: correo electrónico válido. Se guarda en minúsculas: "Ana@Ejemplo.com" y
  "ana@ejemplo.com" son la misma cuenta.
- `password`: de 8 a 100 caracteres, al menos una mayúscula y un número.
- `acepta_aviso`: debe ser `true` (aceptación del aviso de privacidad).
- `declara_edad`: debe ser `true` (declaración de ser mayor de 18 años o de contar con el
  consentimiento de la madre, padre o persona encargada).

El registro público siempre crea cuentas con rol `usuario`; ninguna ruta de la API permite elevar
el rol.

**Respuesta de registro, login y cambio de contraseña:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

Para obtener los datos de la cuenta se consulta `GET /api/auth/me`.

**Errores:**

| HTTP | Mensaje |
|---|---|
| 409 | "El correo electrónico ya está registrado." |
| 422 | "Debes aceptar el aviso de privacidad para registrarte." |
| 422 | "Debes declarar que eres mayor de 18 años o que cuentas con el consentimiento de tu madre, padre o persona encargada." |
| 422 | "Debe contener al menos una letra mayúscula." / "Debe contener al menos un número." (contraseña) |
| 429 | Límite de solicitudes excedido |

> Los mensajes de las casillas y de la contraseña llegan dentro del formato de error de validación
> (ver [Formato de error](#formato-de-error)).

#### `POST /api/auth/login` — HTTP 200

**Body:**
```json
{
  "email": "jairo@ejemplo.com",
  "password": "MiClave123"
}
```

**Respuesta:** igual a la del registro.

El correo no distingue mayúsculas: se busca en minúsculas, igual que se guarda en el registro.

**Errores:**

| HTTP | Mensaje |
|---|---|
| 401 | "Credenciales inválidas." (correo o contraseña incorrectos, o cuenta desactivada) |
| 422 | Correo con formato inválido o campos faltantes |
| 429 | Límite de solicitudes excedido |

#### `POST /api/auth/logout` — HTTP 200

Sin body. Revoca el token con el que se hace la solicitud hasta su expiración natural.

**Respuesta:**
```json
{
  "message": "Sesión cerrada exitosamente."
}
```

#### `GET /api/auth/me` — HTTP 200

**Respuesta (también de `PATCH /api/auth/me`):**
```json
{
  "id": 1,
  "nombre": "Jairo Castillo",
  "email": "jairo@ejemplo.com",
  "role": "usuario"
}
```

`role` es `usuario` o `administrador`.

#### `PATCH /api/auth/me` — HTTP 200

Solo el nombre es editable; el correo no se modifica. Los espacios al inicio y al final se eliminan.

**Body:**
```json
{
  "nombre": "Jairo A. Castillo"
}
```

**Errores:** 422 si el nombre tiene menos de 2 o más de 100 caracteres.

#### `DELETE /api/auth/me` — HTTP 204

Elimina la cuenta y todos sus análisis de forma definitiva. El token actual se revoca y los demás
tokens de la cuenta dejan de servir (HTTP 401). Se pide la contraseña para confirmar que quien
elimina es el titular.

**Body:**
```json
{
  "password": "MiClave123"
}
```

**Respuesta:** sin contenido.

**Errores:**

| HTTP | Mensaje |
|---|---|
| 400 | "La contraseña es incorrecta." |
| 400 | "No puedes eliminar tu cuenta porque eres el único administrador activo." |
| 409 | "Espera a que termine el análisis en curso antes de eliminar tu cuenta." |
| 429 | Límite de solicitudes excedido |

#### `POST /api/auth/change-password` — HTTP 200

Cambia la contraseña, cierra todas las sesiones de la cuenta y devuelve un token nuevo para que la
sesión desde la que se hizo el cambio continúe.

**Body:**
```json
{
  "password_actual": "MiClave123",
  "password_nueva": "OtraClave456",
  "confirmar_password": "OtraClave456"
}
```

`password_nueva` sigue las mismas reglas que en el registro.

**Respuesta:** igual a la del registro (token nuevo).

**Errores:**

| HTTP | Mensaje |
|---|---|
| 400 | "La contraseña actual es incorrecta." |
| 400 | "La nueva contraseña debe ser distinta de la actual." |
| 422 | "La confirmación no coincide con la nueva contraseña." |
| 422 | "Debe contener al menos una letra mayúscula." / "Debe contener al menos un número." |
| 429 | Límite de solicitudes excedido |

---

### Ingesta — `/api/ingesta`

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/api/ingesta/texto` | Recibe y limpia texto plano de política | Usuario | 20/min |
| POST | `/api/ingesta/url` | Descarga y extrae texto desde URL | Usuario | 10/min |
| POST | `/api/ingesta/archivo` | Extrae texto de un archivo PDF o TXT | Usuario | 10/min |

Las tres vías aplican la misma regla de longitud **sobre el texto ya limpio** (espacios y saltos de
línea normalizados): mínimo **200 caracteres y 40 palabras**, máximo **300,000 caracteres**. La
ingesta no guarda nada: el texto se devuelve para que el usuario lo revise antes de analizarlo.

**Body `POST /texto`:**
```json
{
  "texto": "Texto de la política de privacidad..."
}
```

El texto crudo admite hasta 400,000 caracteres antes de la limpieza.

**Body `POST /url`:**
```json
{
  "url": "https://ejemplo.com/politica-de-privacidad"
}
```

La URL debe tener al menos 10 caracteres y devolver HTML; se extrae el contenido principal de la
página (sin scripts, menús, encabezados ni pies de página).

Para que el servidor no pueda usarse para consultar servicios internos, solo se descargan sitios
web públicos:

- esquema `http` o `https`;
- puerto estándar (80, 443 o sin puerto explícito);
- sin usuario ni contraseña en la URL;
- el nombre del sitio debe resolver únicamente a direcciones IP públicas.

Las redirecciones se siguen una a una (máximo 5) y cada destino se valida con las mismas reglas.

**Body `POST /archivo`:** `multipart/form-data` con el campo `archivo`.

- Formatos: `.pdf` (`application/pdf`) o `.txt` (`text/plain`); la extensión y el tipo deben
  coincidir.
- Tamaño máximo: **5 MB**. El archivo se procesa solo en memoria y se descarta al terminar.
- Los TXT pueden estar en UTF-8 o Windows-1252.
- Los PDF escaneados (sin capa de texto) no se pueden leer.

**Respuesta (las tres vías) — HTTP 200:**
```json
{
  "texto_procesado": "Texto normalizado listo para análisis...",
  "caracteres": 8230,
  "palabras": 1250,
  "fuente": "texto_directo",
  "deteccion": {
    "resultado": "politica",
    "temas_encontrados": ["datos personales", "privacidad", "finalidad", "terceros", "derechos"],
    "temas_total": 10,
    "cobertura": 0.92,
    "voz_responsable": 48
  }
}
```

`fuente` vale `"texto_directo"`, la URL indicada o el nombre del archivo, según la vía.

`deteccion` indica si el texto parece una política de privacidad (RN-18): `politica`, o
`dudosa` si no es seguro (el cliente debe pedir confirmación antes de analizarlo). Un texto
que claramente no lo es se rechaza con 422 y no llega a esta respuesta.

**Errores:**

| HTTP | Ruta | Mensaje |
|---|---|---|
| 413 | archivo | "El archivo supera el tamaño máximo de 5 MB." |
| 415 | archivo | "Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt)." |
| 422 | todas | "El texto debe tener al menos 200 caracteres y 40 palabras." |
| 422 | todas | "Esta política tiene N caracteres y el máximo es 300,000. Las políticas muy extensas suelen tener una sección por cada producto o servicio: copia solo la parte general o la del servicio que usas y pégala en «Pegar texto»." |
| 422 | todas | "El texto no parece una política de privacidad: no explica qué datos personales se recopilan, para qué se usan ni con quién se comparten." |
| 422 | archivo | "No se encontró texto en el PDF. Si es un documento escaneado, el sistema no puede leerlo: copia el texto de la política y pégalo directamente." |
| 422 | url | "La dirección debe comenzar con http:// o https://." |
| 422 | url | "La dirección indicada no es un sitio web público." (puerto no estándar, credenciales en la URL o IP no pública) |
| 422 | url | "La URL redirige demasiadas veces." (más de 5 redirecciones) |
| 422 | url | "La URL tardó demasiado en responder." |
| 422 | url | "No se pudo conectar a la URL proporcionada." (también si el nombre del sitio no se puede resolver) |
| 422 | url | "La URL devolvió el estado HTTP {código}." |
| 422 | url | "Error al acceder a la URL." |
| 422 | url | "La URL no devolvió contenido HTML. Tipo recibido: {tipo}" |
| 422 | url | "No se encontró contenido de texto en la página." |
| 422 | url | "La página no contiene texto extraíble." |
| 429 | todas | Límite de solicitudes excedido |

> **Nota:** Si la página se construye con JavaScript en el navegador (SPA), normalmente no contiene
> texto suficiente y se rechaza con HTTP 422. En ese caso conviene copiar y pegar el texto.

---

### Análisis — `/api/analisis`

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/api/analisis/iniciar` | Crea el análisis y lo procesa en segundo plano | Usuario | 5/min |
| GET | `/api/analisis/{id}/estado` | Progreso de un análisis | Usuario | — |
| GET | `/api/analisis/{id}` | Resultado de un análisis completado | Usuario | — |
| GET | `/api/analisis` | Historial paginado del usuario, con filtros | Usuario | — |
| GET | `/api/analisis/estadisticas` | Totales para el panel estadístico | Usuario | — |
| GET | `/api/analisis/{id}/pdf` | Descarga el reporte en PDF | Usuario | 10/min |
| DELETE | `/api/analisis/{id}` | Elimina de forma definitiva un análisis propio | Usuario | — |

Cada usuario solo puede consultar, descargar o eliminar sus propios análisis. Un análisis ajeno se
responde igual que uno inexistente (HTTP 404).

Si el servidor se reinicia mientras un análisis se procesa, ese análisis no puede continuar: al
arrancar, el servidor marca como `error` todos los que quedaron en `procesando`.

#### `POST /api/analisis/iniciar` — HTTP 202

**Body:**
```json
{
  "texto": "Texto limpio de la política (el texto_procesado de la ingesta)...",
  "confirma_politica": false
}
```

`confirma_politica` (opcional, `false` por defecto) es obligatorio en `true` cuando el texto es
dudoso: la persona confirmó en la vista previa que es una política de privacidad.

Se aplica la misma regla de longitud que en la ingesta (200 caracteres y 40 palabras como mínimo,
300,000 caracteres como máximo). El análisis usa el texto completo; en la base solo se conservan los
primeros 2,000 caracteres.

**Respuesta:**
```json
{
  "id_analisis": "42",
  "estado": "procesando"
}
```

El cliente debe consultar `GET /api/analisis/{id}/estado` hasta que el estado sea `completado` y
luego pedir `GET /api/analisis/{id}`.

> El procesamiento tarda de unos segundos a un par de minutos según el número de secciones y la
> latencia del modelo de lenguaje (OpenAI).

**Errores:** 422 por la regla de longitud o porque el texto no parece una política (mismos
mensajes que la ingesta); 422 "No es seguro que el texto sea una política de privacidad. Confirma
que lo es para analizarlo." si es dudoso y no se envió `confirma_politica: true`; 429 por límite de
solicitudes.

#### `GET /api/analisis/{id}/estado` — HTTP 200

```json
{
  "estado": "procesando",
  "seccion_actual": 3,
  "secciones_total": 14,
  "motivo": null
}
```

- `estado`: `procesando`, `completado` o `error`.
- `motivo`: `"no_es_politica"` si el análisis terminó con error porque casi ninguna sección
  trata del uso de datos personales (el texto no recibe puntuación); `null` en los demás casos.
- `seccion_actual`: secciones ya analizadas.
- `secciones_total`: total de secciones; `null` mientras aún no se ha dividido el texto.

**Errores:** 404 "Análisis no encontrado."

#### `GET /api/analisis/{id}` — HTTP 200

Devuelve el resultado completo (ver [Estructura del resultado](#estructura-del-resultado-del-análisis)).

**Errores:**

| HTTP | Mensaje |
|---|---|
| 404 | "Análisis no encontrado." (inexistente o ajeno) |
| 409 | "El análisis todavía se está procesando." |
| 409 | "El análisis no pudo completarse. Intenta analizar la política de nuevo." (terminó con error) |

#### `GET /api/analisis` — HTTP 200

Lista los análisis **completados** del usuario, más recientes primero.

**Parámetros de consulta (todos opcionales):**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `page` | entero ≥ 1 | Página (por defecto 1) |
| `page_size` | entero de 1 a 50 | Elementos por página (por defecto 10) |
| `nivel` | `bajo` \| `medio` \| `alto` | Nivel de riesgo global |
| `desde` | fecha y hora ISO 8601 | Desde esta fecha y hora, inclusive |
| `hasta` | fecha y hora ISO 8601 | Hasta esta fecha y hora, inclusive |
| `q` | texto, máx. 100 caracteres | Busca en el texto guardado de la política o en el comentario del resumen |

- Las fechas sin zona horaria se interpretan como UTC. El cliente web convierte el día local del
  usuario a UTC antes de enviarlo.
- La búsqueda `q` no distingue mayúsculas ni acentos, y los caracteres `%` y `_` se buscan de forma
  literal.

**Ejemplo:** `GET /api/analisis?nivel=alto&desde=2026-09-01T06:00:00Z&q=terceros`

**Respuesta:**
```json
{
  "items": [
    {
      "id_analisis": "42",
      "fecha": "2026-09-30T14:30:00Z",
      "nivel_riesgo_global": "alto",
      "puntaje": 72,
      "comentario_breve": "Se detectaron varios hallazgos de riesgo alto..."
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

**Errores:**

| HTTP | Mensaje |
|---|---|
| 422 | "La fecha inicial no puede ser posterior a la fecha final." |
| 422 | Parámetros inválidos (nivel fuera de la lista, fecha mal escrita, `page_size` > 50, `q` > 100 caracteres) |

#### `GET /api/analisis/estadisticas` — HTTP 200

Totales de los análisis del usuario para el panel estadístico.

```json
{
  "total": 12,
  "por_nivel": { "bajo": 3, "medio": 6, "alto": 3 },
  "puntaje_promedio": 54.5
}
```

Sin análisis, todos los valores son 0.

#### `GET /api/analisis/{id}/pdf` — HTTP 200

Genera el reporte del análisis y lo devuelve como `application/pdf`, con el header
`Content-Disposition: attachment; filename="privapp-analisis-{id}.pdf"`.

**Errores:** los mismos que `GET /api/analisis/{id}` (404 si es inexistente o ajeno; 409 si todavía
se está procesando o terminó con error); 429 por límite de solicitudes.

#### `DELETE /api/analisis/{id}` — HTTP 204

Elimina el análisis de forma definitiva. Respuesta sin contenido.

**Errores:**

| HTTP | Mensaje |
|---|---|
| 404 | "Análisis no encontrado." |
| 409 | "No se puede eliminar un análisis que todavía se está procesando." |

---

### Estructura del resultado del análisis

Respuesta de `GET /api/analisis/{id}`:

```json
{
  "id_analisis": "42",
  "fecha": "2026-09-30T14:30:00Z",
  "resumen_general": {
    "nivel_riesgo_global": "medio",
    "puntaje": 55,
    "comentario_breve": "Se detectaron 3 hallazgos de riesgo medio..."
  },
  "secciones_analizadas": [
    {
      "categoria_opp115": "Third Party Sharing/Collection",
      "titulo": "Compartición con terceros",
      "texto_original": "Fragmento de la política analizado...",
      "hallazgos": [
        {
          "tipo": "riesgo",
          "descripcion": "Se comparten datos con terceros no identificados.",
          "nivel": "alto",
          "criterio": "A4",
          "tipo_tratamiento": "Transferencia de datos a terceros",
          "sin_respaldo": false,
          "fuentes_normativas": [
            {
              "documento": "Principios OEA 2021",
              "referencia": "Principio 5",
              "fragmento_relevante": "Extracto real del documento del corpus...",
              "jurisdiccion": "internacional"
            }
          ]
        }
      ],
      "analizada": true
    }
  ],
  "recomendaciones": [
    "Revisa con qué empresas se comparten tus datos antes de aceptar.",
    "Desactiva el uso de tus datos con fines publicitarios desde la configuración de tu cuenta."
  ]
}
```

**`resumen_general`**

| Campo | Tipo | Descripción |
|---|---|---|
| `nivel_riesgo_global` | `bajo` \| `medio` \| `alto` | Nivel de riesgo de la política |
| `puntaje` | entero 0–100 | Puntuación de riesgo |
| `comentario_breve` | texto | Resumen en una o dos frases |

**Sección (`secciones_analizadas[]`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `categoria_opp115` | texto | Categoría de la taxonomía OPP-115 |
| `titulo` | texto | Título de la sección |
| `texto_original` | texto | Fragmento de la política analizado |
| `hallazgos` | lista | Hallazgos de la sección |
| `analizada` | booleano | `false` si la sección no pudo analizarse (respuesta inválida o error del modelo): muestra el aviso "No fue posible analizar esta sección automáticamente." y no cuenta para el nivel global ni para el puntaje. Los análisis anteriores no traen el campo y se toman como `true` |

**Hallazgo (`hallazgos[]`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `tipo` | `riesgo` \| `transparencia` \| `neutral` | Tipo de hallazgo |
| `descripcion` | texto | Descripción en lenguaje sencillo |
| `nivel` | `bajo` \| `medio` \| `alto` | Nivel del hallazgo |
| `criterio` | texto o `null` | Código del criterio de la rúbrica que cumple la cláusula: `A1`–`A10` (riesgo alto), `M1`–`M5` (riesgo medio), `B1`–`B4` (buena práctica, nivel bajo). `tipo` y `nivel` se derivan de él. `null` en análisis anteriores y en secciones que no pudieron analizarse |
| `tipo_tratamiento` | texto o `null` | Tipo de tratamiento de datos (lista cerrada, ver abajo). `null` solo en análisis realizados antes de incorporar la clasificación |
| `sin_respaldo` | booleano | `true` si ningún fragmento del corpus normativo respalda el hallazgo: se muestra marcado y no cuenta para el nivel global ni para el puntaje (sí para las recomendaciones) |
| `fuentes_normativas` | lista | Citas del corpus normativo que respaldan el hallazgo (vacía si `sin_respaldo` es `true`) |

Valores posibles de `tipo_tratamiento`:

- `Recopilación de datos personales`
- `Uso y finalidad de los datos`
- `Transferencia de datos a terceros`
- `Tiempo de conservación de los datos`
- `Seguridad de los datos`
- `Derechos del usuario sobre sus datos`
- `Cambios en la política`
- `Otro`

**Fuente normativa (`fuentes_normativas[]`)**

Las citas las arma el servidor a partir de los fragmentos reales del corpus que el modelo indica; el
modelo no redacta el texto citado.

| Campo | Tipo | Descripción |
|---|---|---|
| `documento` | texto | Nombre del documento fuente |
| `referencia` | texto | Artículos o principios detectados en el fragmento |
| `fragmento_relevante` | texto | Extracto real del fragmento (hasta 600 caracteres) |
| `jurisdiccion` | texto o `null` | Jurisdicción del fragmento (`guatemala`, `internacional` o `estandar_tecnico`). `null` en análisis anteriores; en ese caso el cliente la deduce del nombre del documento |

**`recomendaciones`:** lista de acciones prácticas redactadas a partir de los riesgos altos y
medios encontrados. Si no hay riesgos de ese tipo o el modelo no responde, se devuelven
recomendaciones básicas generadas sin el modelo.

---

### Administración — `/api/admin`

Todas las rutas requieren rol **Administrador**. Una cuenta sin ese rol recibe HTTP 403
"No tienes permisos para acceder a este recurso."

| Método | Ruta | Descripción | Auth | Rate limit |
|---|---|---|---|---|
| GET | `/api/admin/usuarios` | Lista paginada de usuarios, con búsqueda | Administrador | — |
| PATCH | `/api/admin/usuarios/{id}/estado` | Activa o desactiva una cuenta | Administrador | — |
| GET | `/api/admin/corpus` | Documentos del corpus normativo | Administrador | — |
| POST | `/api/admin/corpus` | Incorpora un documento normativo nuevo | Administrador | 5/min |
| PATCH | `/api/admin/corpus/estado` | Activa o desactiva un documento completo | Administrador | — |

#### `GET /api/admin/usuarios` — HTTP 200

**Parámetros de consulta:** `page` (≥ 1, por defecto 1), `page_size` (1 a 50, por defecto 10) y
`q` (máx. 100 caracteres; busca por nombre o correo sin distinguir mayúsculas ni acentos). El
listado se ordena por id y nunca incluye el contenido de los análisis.

```json
{
  "items": [
    {
      "id": 1,
      "nombre": "Jairo Castillo",
      "email": "jairo@ejemplo.com",
      "role": "usuario",
      "is_active": true,
      "created_at": "2026-09-01T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

#### `PATCH /api/admin/usuarios/{id}/estado` — HTTP 200

**Body:**
```json
{
  "activo": false
}
```

Al desactivar una cuenta se invalidan todas sus sesiones y ya no puede iniciar sesión.

**Respuesta:** el usuario actualizado (mismo formato que un elemento de `items`).

**Errores:**

| HTTP | Mensaje |
|---|---|
| 400 | "No puedes desactivar tu propia cuenta." |
| 404 | "Usuario no encontrado." |

#### `GET /api/admin/corpus` — HTTP 200

```json
{
  "documentos": [
    {
      "documento_fuente": "decreto_57_2008.pdf",
      "jurisdiccion": "guatemala",
      "fragmentos": 84,
      "fecha_carga": "2026-08-15T12:00:00Z",
      "activo": true
    }
  ]
}
```

Solo los documentos activos se usan en la recuperación de fragmentos durante el análisis.

#### `POST /api/admin/corpus` — HTTP 201

**Body:** `multipart/form-data` con:

- `archivo`: documento en `.pdf` o `.txt`, máximo 5 MB. El nombre del archivo es el identificador
  del documento (`documento_fuente`).
- `jurisdiccion`: `guatemala`, `internacional` o `estandar_tecnico`.

El documento se divide en fragmentos, se generan sus representaciones vectoriales y queda activo.
El archivo original se descarta. Como cada carga genera representaciones vectoriales, se admiten
como máximo 5 cargas por minuto. Un envío cuyo `Content-Length` supere 6 MB (5 MB del archivo más
margen para el formulario) se rechaza con 413 antes de leerlo, igual que en la ingesta de archivos.

**Respuesta:**
```json
{
  "documento_fuente": "nuevo_documento.pdf",
  "jurisdiccion": "internacional",
  "fragmentos": 40,
  "fecha_carga": "2026-09-30T15:00:00Z",
  "activo": true,
  "fragmentos_insertados": 40,
  "fragmentos_duplicados": 0
}
```

**Errores:**

| HTTP | Mensaje |
|---|---|
| 409 | "Ya existe un documento con ese nombre en el corpus normativo." |
| 413 | "El archivo supera el tamaño máximo de 5 MB." |
| 415 | "Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt)." |
| 422 | "El documento no contiene texto suficiente para incorporarlo al corpus (mínimo 50 palabras)." |
| 422 | `jurisdiccion` fuera de la lista o campos faltantes |
| 429 | Límite de solicitudes excedido |

#### `PATCH /api/admin/corpus/estado` — HTTP 200

Activa o desactiva todos los fragmentos de un documento, sin modificar su texto.

**Body:**
```json
{
  "documento_fuente": "decreto_57_2008.pdf",
  "activo": false
}
```

**Respuesta:** el documento actualizado (mismo formato que un elemento de `documentos`).

**Errores:** 404 "Documento no encontrado en el corpus normativo."

---

## Códigos de error

Errores comunes a todas las rutas protegidas:

| HTTP | Mensaje | Descripción |
|---|---|---|
| 401 | "Token de autenticación inválido o expirado." | Token inválido, expirado, revocado, anterior a un cambio de contraseña o de una cuenta inactiva o eliminada |
| 403 | "Not authenticated" | Sin token en el header Authorization |
| 403 | "No tienes permisos para acceder a este recurso." | Ruta de administración con una cuenta sin ese rol |
| 422 | (lista de errores de validación) | Cuerpo o parámetros que no cumplen el esquema |
| 429 | "Demasiadas solicitudes. Espera un minuto antes de volver a intentarlo." | Límite de solicitudes excedido |

Resumen por código:

| HTTP | Uso |
|---|---|
| 400 | Contraseña incorrecta, contraseña repetida, autodesactivación o único administrador |
| 401 | Credenciales o token inválidos |
| 403 | Sin token o sin rol de administrador |
| 404 | Análisis, usuario o documento del corpus no encontrado (o ajeno) |
| 409 | Correo ya registrado, documento del corpus repetido, análisis en curso o análisis que terminó con error |
| 413 | Archivo mayor de 5 MB |
| 415 | Archivo que no es PDF ni TXT |
| 422 | Datos de entrada inválidos (texto demasiado corto o largo, URL inaccesible, PDF sin texto, fechas invertidas, etc.) |
| 429 | Límite de solicitudes excedido |

Los fallos del modelo de lenguaje (OpenAI) durante el análisis no se devuelven como error HTTP: la
sección afectada se resuelve con una sección de respaldo y, si falla el proceso completo, el
análisis queda con `estado: "error"` en `GET /api/analisis/{id}/estado` (y `GET /api/analisis/{id}`
responde 409).

### Formato de error

Los errores de la aplicación usan:
```json
{
  "detail": "Mensaje descriptivo del error."
}
```

Los errores de validación del esquema (HTTP 422 generados por FastAPI) devuelven `detail` como una
lista con el mismo formato de FastAPI; el mensaje está en `msg` (en las reglas propias, sin el
prefijo "Value error, " que agrega Pydantic):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Debe contener al menos un número.",
      "input": "MiClaveSegura"
    }
  ]
}
```

El error de límite de solicitudes (HTTP 429) usa el mismo formato:
```json
{
  "detail": "Demasiadas solicitudes. Espera un minuto antes de volver a intentarlo."
}
```

---

## Flujo de integración recomendado

```
1. POST /api/auth/register (o /login)       →  obtener token
2. POST /api/ingesta/texto | url | archivo  →  obtener texto_procesado (vista previa para el usuario)
3. POST /api/analisis/iniciar (con texto_procesado)  →  obtener id_analisis (estado "procesando")
4. GET  /api/analisis/{id}/estado  (repetir cada pocos segundos)  →  hasta "completado" o "error"
5. GET  /api/analisis/{id}  →  resultado completo para mostrar al usuario
6. GET  /api/analisis/{id}/pdf  →  reporte descargable (opcional)
```
