# TICKET-04 — Uso consistente de la paleta semántica `riesgo.*` en el cliente

**Prioridad:** Baja
**Complejidad:** Baja
**Área:** Frontend — sistema de diseño / componentes de visualización
**Requiere decisión humana:** No
**Dependencias:** Ninguna

---

## Situación actual

En la configuración de Tailwind CSS del cliente (`frontend/tailwind.config.js` o equivalente) hay declarada una paleta de colores semántica bajo la clave `riesgo` (colores tipo semáforo: alto/medio/bajo, en rojo/amarillo/verde). Sin embargo, varios componentes de React que muestran el nivel de riesgo usan clases de Tailwind **estándar** (por ejemplo `bg-green-500`, `bg-yellow-500`, `bg-red-500`, `text-red-600`, etc.) en lugar de las clases semánticas declaradas.

Esto significa que la paleta semántica existe pero está subutilizada, y un cambio futuro de colores de riesgo obligaría a editar cada componente en vez de un solo lugar.

## Objetivo

Reemplazar el uso de clases de color estándar de Tailwind (cuando representan nivel de riesgo) por las clases semánticas ya declaradas en la configuración (`riesgo.*`), de modo que el color de riesgo se controle desde un único punto.

## Qué hacer

1. Abre la configuración de Tailwind y confirma los nombres exactos de las clases semánticas declaradas bajo `riesgo` (por ejemplo, podrían ser `riesgo-alto`, `riesgo-medio`, `riesgo-bajo`, o una escala numérica — usa los nombres reales que encuentres).
2. Identifica los componentes que representan visualmente el nivel de riesgo. Candidatos probables (verifica los nombres reales en `frontend/src/`):
   - El indicador tipo semáforo / medidor de puntaje.
   - Las tarjetas o etiquetas de hallazgos por sección que se colorean según severidad.
   - Cualquier badge/etiqueta de nivel de riesgo en la pantalla de resultados o en el historial.
3. En esos componentes, reemplaza las clases estándar que representan riesgo por las clases semánticas correspondientes.
4. Comprueba visualmente (o mediante las pruebas de frontend si existen) que los colores se sigan viendo correctamente después del cambio.

## Criterios de aceptación

- Los componentes que muestran nivel de riesgo usan las clases `riesgo.*` declaradas, no clases de color genéricas de Tailwind.
- El resultado visual es equivalente al anterior (mismos colores para los mismos niveles).
- Si el proyecto tiene pruebas de frontend, siguen en verde.

## Fuera de alcance

- No cambies los valores de color de la paleta `riesgo` (no es un rediseño; es alinear el uso con lo ya declarado). Si crees que un color debería cambiar, anótalo como observación, no lo modifiques.
- No toques colores que **no** representan nivel de riesgo (colores de marca, fondos neutros, botones primarios, etc.). Solo los relacionados con la comunicación del riesgo.
- No refactorices la estructura de los componentes; solo cambia las clases de color pertinentes.
