# Corpus Normativo

Este directorio contiene los documentos legales y estándares técnicos que alimentan
la recuperación semántica (RAG) del motor de análisis. Los documentos **están
incluidos en el repositorio**.

## Estructura

Solo se cargan los archivos que están dentro de una carpeta de jurisdicción. La
carpeta determina la jurisdicción con la que se citan los fragmentos.

```
corpus_normativo/
├── guatemala/                         → jurisdicción "guatemala"
│   ├── Constitución Política de la República de Guatemala.pdf
│   └── Decreto 57-2008 (Ley de Acceso a la Información Pública).pdf
├── internacional/                     → jurisdicción "internacional"
│   ├── LOPDP España.pdf
│   ├── Ley Modelo Parlatino 2022.pdf
│   ├── Principios OEA 2021.txt
│   └── RGPD.pdf
├── estandares_tecnicos/               → jurisdicción "estandar_tecnico"
│   ├── El Corpus OPP-115 y su Ontología Estructural.pdf
│   ├── Metodología, Casuística y Algoritmos del Proyecto ToS;DR.pdf
│   └── tosdr_metodologia.md
└── originales/                        → no se carga (documentos fuente)
    └── Principios OEA 2021.pdf
```

El nombre del archivo, sin la extensión, es el nombre con el que el documento
aparece en las citas (por ejemplo, "Principios OEA 2021").

### Principios OEA 2021

El PDF oficial está maquetado en pliegos (dos páginas del libro por página del PDF)
con texto a dos columnas, y su extracción directa mezclaba las columnas. Por eso se
carga `internacional/Principios OEA 2021.txt`, obtenido de ese mismo PDF extrayendo
cada página del libro por separado, uniendo las palabras cortadas con guion al final
de línea y quitando los números de página y los encabezados repetidos. El PDF
original se conserva en `originales/` como fuente.

## Fuentes oficiales

| Documento | Fuente oficial |
|---|---|
| Constitución Política de la República de Guatemala | Organismo Judicial de Guatemala |
| Decreto 57-2008 LAIP | Ministerio de Gobernación / IDPP Guatemala |
| RGPD | EUR-Lex: eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX%3A32016R0679 |
| LOPDP España | BOE: boe.es/buscar/act.php?id=BOE-A-2018-16673 |
| Principios OEA 2021 | OEA: oas.org/es/sla/ddi/proteccion-datos-personales.asp |
| Ley Modelo Parlatino | parlatino.org |
| OPP-115 | lorrie.cmu.edu/research/usableprivacy/db/ |

## Cargar el corpus

```bash
docker compose exec backend python scripts/cargar_corpus.py
```

El script acepta PDF, TXT y MD, y es idempotente: no duplica fragmentos que ya
estén cargados (los compara por su hash). Si se reemplaza un documento por otra
versión con otro nombre de archivo, hay que eliminar antes los fragmentos del
documento anterior, o desactivarlo desde **Administración → Corpus normativo**.

En producción, la imagen del servidor no incluye este directorio: los documentos se
cargan desde **Administración → Corpus normativo** (PDF o TXT de hasta 5 MB; un
archivo `.md`, como `tosdr_metodologia.md`, se carga guardándolo como `.txt`).

## Notas importantes

- Guatemala **no tiene** una ley integral de protección de datos personales.
  El corpus guatemalteco son la Constitución y la LAIP, que aplican de forma
  parcial a la privacidad de datos.
- Las normativas internacionales se usan como **referencia de buenas prácticas**,
  no como derecho vigente en Guatemala. El sistema lo indica explícitamente en
  cada análisis.
