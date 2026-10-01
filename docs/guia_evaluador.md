# Guía del Evaluador — PrivApp

**Documento para:** Asesora Sheyla Esquivel y tribunal evaluador del Proyecto de Graduación II  
**Autor:** Jairo Ardani Castillo Girón — castillo.jairo99930@gmail.com  
**Carné:** 0905-22-12005 | UMG Campus Jutiapa  
**Actualizado:** septiembre de 2026

---

## ¿Qué hace el sistema?

PrivApp analiza automáticamente políticas de privacidad de servicios digitales y presenta
los resultados en lenguaje claro para jóvenes de San José Acatempa, Jutiapa.

El flujo completo es:

1. **El usuario se registra** (acepta el aviso de privacidad y declara su edad o el
   consentimiento de su madre, padre o persona encargada) e inicia sesión.
2. **Ingresa la política** pegando el texto, indicando la URL de la página o cargando un
   archivo PDF o TXT.
3. **Revisa la vista previa** del texto obtenido y confirma que es la política correcta.
4. **El sistema divide** la política completa en secciones (las secciones largas o el texto
   sin títulos se dividen en bloques) y las analiza en paralelo.
5. **Para cada sección**, busca en el corpus normativo los fragmentos más relevantes
   (pgvector) e incluye siempre normativa guatemalteca.
6. **Envía a OpenAI (`gpt-4o-mini`)** la sección junto con esos fragmentos; el modelo solo
   indica qué fragmentos respaldan cada hallazgo y el servidor arma la cita con el texto
   real del corpus y su jurisdicción.
7. **Presenta el análisis**: nivel y puntuación de riesgo, hallazgos con tipo de tratamiento,
   citas verificables, recomendaciones prácticas y reporte PDF descargable.

---

## Módulos del sistema

| Módulo | Descripción |
|---|---|
| Autenticación y sesiones | Registro con aviso y declaración de edad, inicio y cierre de sesión, revocación de sesiones |
| Ingesta de políticas | Texto, URL o archivo PDF/TXT (máximo 5 MB), con vista previa obligatoria |
| Motor de análisis | RAG sobre el corpus normativo + OpenAI, cobertura de la política completa |
| Visualización de resultados | Semáforo, puntuación, filtros, citas con jurisdicción, ayuda del glosario |
| Reportes | Descarga del análisis en PDF |
| Historial | Consulta con filtros y eliminación definitiva de análisis |
| Panel estadístico | Resumen personal de los análisis en la pantalla principal |
| Perfil | Edición del nombre, cambio de contraseña y eliminación de la cuenta |
| Glosario y aviso de privacidad | Páginas públicas de consulta |
| Administración | Gestión de usuarios y del corpus normativo (solo administradores) |

---

## Requisitos para ejecutar el sistema

1. **Docker Desktop** instalado y en ejecución.
2. Archivo `.env` creado a partir de `.env.example` (ver `docs/instalacion.md`), con
   `LLM_PROVIDER=openai`, una API key válida en `OPENAI_API_KEY` y `OPENAI_MODEL=gpt-4o-mini`.
3. Documentos del corpus normativo colocados en `corpus_normativo/guatemala/`,
   `corpus_normativo/internacional/` y `corpus_normativo/estandares_tecnicos/`
   (ver `corpus_normativo/README.md`).

> En local, Docker Compose levanta su propio Redis. El `REDIS_URL` de `.env.example`
> (`redis://redis:6379/0`) ya apunta a ese servicio, así que funciona sin cambios.

---

## Cómo preparar el sistema

### Paso 1: Levantar el sistema

```bash
docker compose up --build
```

Esperar hasta ver en los registros:
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

La carga del corpus es idempotente: si se repite, no duplica fragmentos.

### Paso 3: Verificar servicios

| URL | Resultado esperado |
|---|---|
| http://localhost:5173 | Pantalla de inicio de sesión de PrivApp |
| http://localhost:8000/health | `{"status": "ok", "service": "privapp-backend", "version": "2.0.0", ...}` |
| http://localhost:8000/docs | Swagger UI con todos los endpoints |

### Paso 4 (opcional): Crear un administrador

El rol de administrador no se asigna desde la interfaz ni desde la API. Primero registre la
cuenta de forma normal (CP-01) y luego ejecute:

```bash
docker compose exec backend python scripts/promover_admin.py correo@ejemplo.com
```

La persona debe **cerrar sesión y volver a iniciarla** para que aparezca la opción
**Administración** en la barra de navegación (el servidor reconoce el rol de inmediato).

---

## Casos de prueba

### CP-01: Registro de usuario nuevo

1. Abrir http://localhost:5173 y hacer clic en **Regístrate aquí**.
2. En el formulario **Crear cuenta**, completar **Nombre completo**, **Correo electrónico**,
   **Contraseña** (mínimo 8 caracteres, una mayúscula y un número) y **Confirmar contraseña**.
3. Intentar enviar sin marcar las casillas: el sistema indica que se debe aceptar el aviso de
   privacidad y declarar la edad o el consentimiento.
4. Marcar **He leído y acepto el aviso de privacidad** (el enlace abre el aviso en otra
   pestaña) y **Soy mayor de 18 años o cuento con el consentimiento de mi madre, padre o
   persona encargada para usar PrivApp**.
5. Hacer clic en **Crear cuenta**.
6. **Resultado esperado:** el sistema inicia sesión automáticamente y muestra la pantalla
   principal con el saludo **Bienvenido, <nombre>**. Un correo ya registrado muestra
   *"Este correo ya está registrado."*, también si solo cambian las mayúsculas (el correo se
   guarda en minúsculas: *Ana@Ejemplo.com* y *ana@ejemplo.com* son la misma cuenta).

### CP-02: Inicio y cierre de sesión

1. Hacer clic en **Salir** en la barra de navegación.
2. Iniciar sesión con las credenciales registradas y el botón **Iniciar sesión**.
3. **Resultado esperado:** acceso a la pantalla principal, aunque el correo se escriba con
   otras mayúsculas. Credenciales incorrectas muestran *"Correo o contraseña incorrectos."*

### CP-03: Rutas protegidas

1. Copiar la URL http://localhost:5173/analizar.
2. Cerrar sesión e intentar abrir la URL copiada.
3. **Resultado esperado:** redirección automática a `/login`. Una cuenta sin rol de
   administrador que abra `/admin` es enviada a la pantalla principal.

### CP-04: Análisis de política por texto (caso principal)

1. En la pantalla principal, hacer clic en la tarjeta **Analizar política**.
2. En la pestaña **Pegar texto**, pegar una política real o el texto de ejemplo al final de
   este documento. El contador indica los caracteres y el mínimo requerido.
3. Hacer clic en **Revisar texto**.
4. En **Revisa el texto antes de analizarlo**, comprobar el origen, los caracteres, las
   palabras y el texto que se analizará. Se puede elegir **Corregir** (vuelve al formulario
   conservando lo ingresado) o **Cancelar** (descarta todo).
5. Hacer clic en **Confirmar y analizar**.
6. **Resultado esperado:** la pantalla **Resultados del análisis** muestra el progreso
   (*"Analizando la política: N de M secciones listas..."*) y un **Consejo de privacidad**
   que cambia cada pocos segundos. Al terminar aparece el resultado (ver CP-07).

### CP-05: Análisis de política por URL

1. En **Analizar política**, seleccionar la pestaña **Desde URL**.
2. Ingresar la URL de una política de privacidad pública y hacer clic en **Revisar texto**.
3. **Resultado esperado:** la vista previa muestra *"Dirección web: <url>"* como origen y el
   texto extraído; al confirmar, se produce el análisis.
4. **Si la URL falla** (por ejemplo, un sitio que carga el contenido con JavaScript), se
   muestra un mensaje de error claro y el usuario puede usar otra pestaña.
5. **Solo sitios web públicos:** ingresar una dirección interna, por ejemplo
   `http://localhost:8000/health` o `http://192.168.1.1`. **Resultado esperado:**
   *"La dirección indicada no es un sitio web público."* Lo mismo ocurre con un puerto
   distinto de 80 o 443 o con usuario y contraseña dentro de la URL. Una dirección que no
   empieza con `http://` o `https://` (por ejemplo, `ftp://ejemplo.com`) muestra
   *"La dirección debe comenzar con http:// o https://."*, y una que redirige más de cinco
   veces, *"La URL redirige demasiadas veces."*

### CP-06: Análisis de política por archivo

1. En **Analizar política**, seleccionar la pestaña **Desde archivo**.
2. Elegir un PDF o TXT de la política (máximo 5 MB) y hacer clic en **Revisar texto**.
3. **Resultado esperado:** la vista previa muestra *"Archivo: <nombre>"* y el texto
   extraído. El archivo no se guarda.
4. Un archivo de otro tipo, mayor de 5 MB o un PDF escaneado sin texto muestran un mensaje
   de error claro.

### CP-07: Revisión de resultados

En la pantalla de resultados, verificar:

1. **Resumen ejecutivo:** fecha, semáforo (**Riesgo Bajo**, **Riesgo Medio** o **Riesgo
   Alto**), **Puntuación de riesgo** de 0 a 100, comentario breve y los indicadores
   **Secciones**, **Hallazgos críticos** y **Recomendaciones**.
2. **Secciones analizadas:** cada sección se expande o contrae; muestra el **Fragmento
   analizado** y sus **Hallazgos** con nivel (alto, medio o bajo), tipo (riesgo,
   transparencia o neutral) y **tipo de tratamiento** (por ejemplo, *Transferencia de datos a
   terceros*). Los análisis anteriores a esta función pueden no mostrar el tipo de tratamiento.
3. **Fuentes normativas:** cada cita muestra la etiqueta de jurisdicción **Guatemala**
   (azul), **Internacional** (morado) o **Estándar técnico** (gris), el documento, los
   artículos detectados y el extracto real del corpus. Las internacionales llevan la nota
   *"Referencia internacional — buena práctica, no ley vigente en Guatemala."*
4. **Hallazgos sin respaldo:** si ningún fragmento del corpus respalda un hallazgo, este se
   marca como **Sin respaldo en el corpus normativo**, no muestra citas y no cuenta para el
   nivel global ni para la puntuación. Tampoco cuentan las secciones que no pudieron
   analizarse (*"No fue posible analizar esta sección automáticamente."*).
5. **Filtros:** en el recuadro de filtros, elegir **Nivel de riesgo** y **Jurisdicción de la
   cita**. Se muestra *"Mostrando X de Y hallazgos"*, las secciones sin coincidencias se
   ocultan (las demás conservan su número) y el resumen ejecutivo no cambia. **Limpiar
   filtros** o **Mostrar todos los hallazgos** restablecen la vista.
6. **Ayuda del glosario:** el ícono de interrogación junto a *Nivel de riesgo*, *Puntuación
   de riesgo*, el tipo de tratamiento, *Recomendaciones* y las notas de citas muestra la
   definición del término y el enlace **Ver en el glosario**.
7. **Recomendaciones:** entre 3 y 5 acciones prácticas redactadas a partir de los riesgos
   altos y medios encontrados. Si no hay riesgos de ese tipo, se muestran recomendaciones
   generales.
8. Al final se muestra el aviso de que el análisis es orientativo y no constituye asesoría
   legal.

### CP-08: Descarga del reporte PDF

1. En los resultados, hacer clic en **Descargar PDF** (mientras se genera, el botón indica
   **Generando PDF...**).
2. **Resultado esperado:** se descarga `privapp-analisis-<id>.pdf` con el resumen, las
   secciones, los hallazgos (incluidos los marcados sin respaldo), las citas con jurisdicción
   y las recomendaciones.

### CP-09: Historial con filtros y eliminación

1. En la pantalla principal, hacer clic en la tarjeta **Mis análisis**.
2. **Resultado esperado:** lista de análisis con fecha, comentario breve, semáforo y
   puntuación; al hacer clic en uno se abren sus resultados.
3. Probar los filtros **Buscar** (texto de la política o del resumen; no distingue acentos),
   **Nivel de riesgo**, **Desde** y **Hasta**, y hacer clic en **Aplicar filtros**. Se
   indica cuántos análisis coinciden; **Limpiar filtros** vuelve a la lista completa. Una
   fecha inicial posterior a la final muestra un mensaje de error.
4. Hacer clic en el ícono de papelera de un análisis y confirmar con **Eliminar** en el
   diálogo **¿Eliminar este análisis?**.
5. **Resultado esperado:** el análisis desaparece de la lista de forma definitiva. También
   puede eliminarse desde sus resultados con **Eliminar análisis**. Un análisis que aún está
   en curso no puede eliminarse.

### CP-10: Panel estadístico

1. Volver a la pantalla principal.
2. **Resultado esperado:** la sección **Mis estadísticas** muestra **Análisis realizados**,
   **Puntuación promedio** y un gráfico de la distribución por nivel (bajo, medio y alto)
   con sus totales. Una cuenta sin análisis muestra ceros y un mensaje explicativo en lugar
   del gráfico.

### CP-11: Perfil

1. Hacer clic en el nombre del usuario en la barra de navegación (en pantallas pequeñas, el
   ícono de persona) para abrir **Mi perfil**.
2. **Datos de la cuenta:** muestra el correo (no se puede modificar) y el rol.
3. **Editar nombre:** cambiar el nombre y hacer clic en **Guardar cambios**. Resultado
   esperado: *"Tu nombre se actualizó correctamente."* y el nombre nuevo en la barra.
4. **Cambiar contraseña:** completar **Contraseña actual**, **Nueva contraseña** y
   **Confirmar nueva contraseña**, y hacer clic en **Cambiar contraseña**. Resultado
   esperado: confirmación de que la contraseña se actualizó y de que se cerraron las
   sesiones abiertas en otros dispositivos. Una contraseña actual incorrecta muestra un
   error en ese campo.
5. **Eliminar mi cuenta** (probar con una cuenta de prueba): escribir la **Contraseña**,
   hacer clic en **Eliminar mi cuenta** y confirmar con **Eliminar definitivamente** en el
   diálogo **¿Eliminar tu cuenta?**. Resultado esperado: se vuelve al inicio de sesión con
   el mensaje *"Tu cuenta y todos tus análisis se eliminaron definitivamente."* No es posible
   eliminar la cuenta con una contraseña incorrecta, con un análisis en curso ni si es la
   del único administrador activo.

### CP-12: Glosario y aviso de privacidad

1. Abrir **Glosario** desde la barra de navegación o el pie de página (también está
   disponible sin iniciar sesión).
2. **Resultado esperado:** la lista de términos con su definición; el campo **Buscar un
   término** filtra la lista e indica cuántos términos coinciden.
3. Abrir **Aviso de privacidad** desde el pie de página o desde el formulario de registro.
4. **Resultado esperado:** el aviso completo, con su fecha de última actualización, visible
   sin iniciar sesión.

### CP-13: Administración de usuarios

Requiere una cuenta promovida a administrador (Paso 4).

1. Hacer clic en **Administración** en la barra de navegación y luego en **Usuarios**.
2. **Resultado esperado:** lista paginada de cuentas con rol, fecha de registro y estado
   (**Activa** o **Desactivada**). La propia cuenta aparece como **Tu cuenta** y no puede
   desactivarse.
3. Buscar con **Buscar por nombre o correo** y el botón **Buscar** (no distingue acentos).
4. Hacer clic en **Desactivar** en otra cuenta y confirmar. Resultado esperado: la persona
   no puede iniciar sesión y se cierran todas sus sesiones activas. **Activar** revierte el
   cambio.

### CP-14: Administración del corpus normativo

1. En **Administración**, hacer clic en **Corpus normativo**.
2. **Resultado esperado:** lista de documentos con jurisdicción, número de fragmentos,
   fecha de carga y estado (**Activo** o **Desactivado**).
3. En **Cargar documento normativo**, elegir un PDF o TXT (máximo 5 MB), seleccionar la
   **Jurisdicción** y hacer clic en **Cargar documento**. El nombre del archivo identifica
   al documento; un documento con un nombre ya cargado es rechazado. Se admiten como máximo
   cinco cargas por minuto.
4. Hacer clic en **Desactivar** en un documento y confirmar. Resultado esperado: sus
   fragmentos dejan de usarse en los análisis nuevos; los análisis ya realizados no cambian.

### CP-15: Visualización en teléfono

1. Abrir las herramientas de desarrollador del navegador (F12).
2. Activar la vista de dispositivo móvil (375 px de ancho).
3. Recorrer el análisis, los resultados, el historial y el perfil.
4. **Resultado esperado:** la interfaz es usable: texto legible, botones accesibles y
   secciones expandibles que funcionan correctamente.

---

## Texto de ejemplo para pruebas (CP-04)

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
Sí. El modelo solo indica los números de los fragmentos del corpus que respaldan cada
hallazgo; el servidor arma la cita con el documento, los artículos detectados, el extracto
real y la jurisdicción. Los números inexistentes se descartan. Si un hallazgo no tiene
respaldo, se muestra marcado como tal en la web y en el PDF y no cuenta para el nivel global
ni para la puntuación.

**¿Qué pasa si el modelo falla o devuelve una respuesta inválida?**  
El sistema vuelve a solicitar la respuesta una vez, indicando el motivo del rechazo. Si aun
así una sección no se puede analizar, se muestra *"No fue posible analizar esta sección
automáticamente."*, el análisis continúa con las demás y el resultado siempre se entrega.
Esa sección no cuenta para el nivel global ni para la puntuación.

**¿Qué pasa si el servidor se reinicia durante un análisis?**
El análisis en curso no puede continuar. Al arrancar, el servidor marca como error los
análisis que quedaron en proceso, y al abrirlos se muestra *"Ocurrió un error durante el
análisis. Intenta nuevamente."*; basta con analizar la política de nuevo.

**¿Cuánto tarda un análisis?**  
Depende de la extensión de la política. En pruebas con políticas reales de 14 a 21
secciones, el análisis tomó menos de un minuto.

**¿Qué datos se almacenan?**  
La cuenta (nombre, correo, contraseña protegida con hash, fecha de aceptación del aviso y de la
declaración de edad) y los análisis del usuario, de los que solo se guardan los primeros
2,000 caracteres del texto de la política. Los archivos cargados no se guardan. Cada
persona puede eliminar sus análisis o su cuenta completa en cualquier momento, y los
registros del servidor no incluyen datos personales.

**¿Por qué se usan referencias internacionales si Guatemala no tiene ley de datos?**  
El sistema distingue explícitamente: las referencias guatemaltecas (Constitución, LAIP) se
presentan como normativa vigente; las internacionales (RGPD, OEA, entre otras) se presentan
como buenas prácticas con nota aclaratoria, y OPP-115 y ToS;DR como estándares técnicos. Cada
sección se analiza siempre junto a fragmentos de normativa guatemalteca. Esto está
documentado en `docs/arquitectura.md`.

**Una prueba automatizada de sesiones falló sola, ¿es un error?**  
En Docker Desktop con WSL2 el reloj del contenedor puede desfasarse unos segundos. Si una
prueba de sesiones falla de forma aislada, repita la suite (y considere ejecutar
`wsl --update`).
