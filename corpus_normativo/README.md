# Corpus Normativo — Instrucciones para el desarrollador

Este directorio contiene los documentos legales y estándares técnicos que alimentan
el sistema RAG del Motor de Análisis. **Los archivos PDF NO están incluidos en el
repositorio** y deben ser colocados manualmente por el desarrollador antes de ejecutar
el script de carga.

## Estructura esperada

```
corpus_normativo/
├── guatemala/
│   ├── constitucion_articulos_24_31.pdf    ← Arts. 24 y 31 CPRG (derecho a privacidad)
│   └── decreto_57_2008_laip.pdf            ← Ley de Acceso a la Información Pública
├── internacional/
│   ├── rgpd_articulos_clave.pdf            ← Artículos clave del RGPD (UE)
│   ├── lopdp_espana.pdf                    ← Ley Orgánica de Protección de Datos España
│   ├── principios_oea_2021.pdf             ← Principios OEA sobre privacidad 2021
│   └── ley_modelo_parlatino_2022.pdf       ← Ley Modelo del Parlamento Latinoamericano
└── estandares_tecnicos/
    ├── opp_115_taxonomia.pdf               ← Taxonomía OPP-115 de prácticas de privacidad
    └── tosdr_metodologia.md                ← Metodología ToS;DR para evaluación de ToS
```

## Cómo obtener los documentos

| Documento | Fuente oficial |
|---|---|
| CPRG Arts. 24 y 31 | Organismo Judicial de Guatemala — pdfs.ujmd.edu.sv |
| Decreto 57-2008 LAIP | Ministerio de Gobernación / IDPP Guatemala |
| RGPD | EUR-Lex: eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX%3A32016R0679 |
| LOPDP España | BOE: boe.es/buscar/act.php?id=BOE-A-2018-16673 |
| Principios OEA 2021 | OEA: oas.org/es/sla/ddi/proteccion-datos-personales.asp |
| Ley Modelo Parlatino | parlatino.org |
| OPP-115 | lorrie.cmu.edu/research/usableprivacy/db/ |

## Cargar el corpus (después de colocar los PDFs)

```bash
docker compose exec backend python scripts/cargar_corpus.py
```

El script es idempotente: si se ejecuta dos veces no duplica registros.

## Notas importantes

- Guatemala **no tiene** una ley integral de protección de datos personales.
  El corpus guatemalteco son los artículos constitucionales y la LAIP, que aplican
  de forma parcial a la privacidad de datos.
- Las normativas internacionales se usan como **referencia de buenas prácticas**,
  no como derecho vigente en Guatemala. El sistema lo indica explícitamente en
  cada análisis.
