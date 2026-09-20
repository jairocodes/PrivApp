# TICKET-05 — Etiqueta textual junto al indicador de riesgo (accesibilidad)

**Prioridad:** Baja
**Complejidad:** Baja
**Área:** Frontend — accesibilidad / componente de visualización de riesgo
**Requiere decisión humana:** No
**Dependencias:** Relacionado con el TICKET-04 (probablemente el mismo componente); ejecútalo después.

---

## Situación actual

El nivel de riesgo se comunica mediante un indicador visual tipo semáforo (color) y un puntaje numérico (0-100). **No está confirmado** si el indicador incluye también una **etiqueta textual** del nivel ("Riesgo alto", "Riesgo medio", "Riesgo bajo") o si depende únicamente del color para comunicar la severidad.

Depender solo del color es un problema de accesibilidad: las personas con daltonismo (o en pantallas con mala reproducción de color) no pueden distinguir el nivel de riesgo si el color es el único canal de información.

## Objetivo

Garantizar que el nivel de riesgo se comunique siempre con una **etiqueta textual visible** además del color, cumpliendo la directriz de accesibilidad documentada en el Capítulo V (5.5.4): no depender exclusivamente del color.

## Qué hacer

1. Localiza el componente que muestra el indicador de riesgo tipo semáforo (verifica el nombre real en `frontend/src/`; candidato probable: un componente tipo `IndicadorSemaforo`, `MedidorRiesgo`, `PuntajeRiesgo` o similar).
2. Comprueba si ya muestra una etiqueta textual del nivel de riesgo visible junto al color/puntaje.
   - **Si ya la tiene:** no hagas cambios de código. Reporta que ya se cumplía y ciérralo como "sin cambios necesarios". (Esto es un resultado válido y esperado; no fuerces un cambio.)
   - **Si no la tiene:** agrega una etiqueta textual visible ("Riesgo alto" / "Riesgo medio" / "Riesgo bajo", o los rótulos que ya use el sistema en español) junto al indicador.
3. Como mínimo adicional de accesibilidad (no sustituto de la etiqueta visible), asegúrate de que el indicador tenga un `aria-label` o texto accesible que exprese el nivel, para lectores de pantalla.
4. Usa los rótulos en español coherentes con el resto de la interfaz. Si el sistema ya tiene definidos los textos de nivel en algún lugar (constantes, i18n), reutilízalos en vez de escribir cadenas nuevas.

## Criterios de aceptación

- El nivel de riesgo es comprensible **sin depender del color**: hay una etiqueta textual visible del nivel.
- El indicador expone también un texto accesible (`aria-label` o equivalente) para lectores de pantalla.
- El resultado visual sigue siendo claro y no rompe el diseño existente.
- Si había pruebas de frontend, siguen en verde.

## Fuera de alcance

- No rediseñes el indicador (no cambies de un medidor circular a barras, etc.). Solo añade el canal textual si falta.
- No cambies los colores (eso es el TICKET-04).
