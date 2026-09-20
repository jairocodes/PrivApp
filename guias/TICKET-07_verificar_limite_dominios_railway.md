# TICKET-07 — Verificar el límite de dominios personalizados según el plan de Railway

**Prioridad:** Baja
**Complejidad:** N/A (no es un cambio de código)
**Área:** Administrativo / infraestructura
**Requiere decisión humana:** Sí (es una verificación humana, no una tarea de código)
**Dependencias:** Solo relevante si se usará un dominio personalizado.

---

## Contexto

Durante la investigación sobre Railway se obtuvo, de una respuesta de soporte en el foro oficial, que los límites de dominios personalizados por servicio serían: Free/Trial = 1, Hobby = 2, Pro = 20. Sin embargo, esa cifra proviene de una respuesta indirecta de soporte y **no** de la página oficial de límites, que no pudo abrirse durante la investigación. Además, se aclaró que un dominio raíz y su subdominio `www` cuentan como dos dominios distintos.

## Objetivo

Confirmar, directamente en la documentación oficial vigente, el límite real de dominios personalizados para el plan que usará el proyecto, antes de asumir la cifra reportada de forma indirecta.

## Qué hacer (tarea humana)

1. Consultar la página oficial de Railway sobre límites de red pública / dominios personalizados (`docs.railway.com`, sección de "custom domain count limits" dentro de la referencia de public networking).
2. Confirmar el límite para el plan que se usará en el proyecto.
3. Si se planea usar un dominio raíz + `www`, recordar que cuentan como dos.
4. Anotar la cifra confirmada y la fecha de consulta.

## Criterio de cierre

- Se ha confirmado (o corregido) el límite de dominios personalizados para el plan del proyecto contra la fuente oficial vigente, con fecha de consulta anotada.

## Nota

Este ticket **no** requiere ningún cambio en el código ni en el repositorio. Existe solo para que la afirmación no quede basada en una fuente indirecta. Si el proyecto usará únicamente el subdominio gratuito `*.up.railway.app`, este ticket puede cerrarse como "no aplica".
