#!/usr/bin/env python3
"""Evalúa la detección de políticas de privacidad con un conjunto de textos etiquetados.

Uso:
    docker compose exec backend python scripts/evaluar_deteccion.py /ruta/a/carpeta

La carpeta contiene archivos .txt (UTF-8) cuyo nombre empieza por la etiqueta
esperada:
    politica_*.txt      políticas de privacidad: deben pasar ("politica")
    parecido_*.txt      términos de servicio, avisos de cookies...: no deben rechazarse
    no_politica_*.txt   textos que no tratan datos personales: deben rechazarse

Muestra, por archivo, los temas encontrados, la cobertura semántica, la voz del
responsable y la decisión, y al final los aciertos por grupo. Sirve para calibrar los umbrales
de app/services/deteccion_politica.py y como evidencia de su precisión.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.deteccion_politica import TEMAS, detectar_politica  # noqa: E402

# Lo que se considera acierto para cada grupo.
ACEPTABLE = {
    "politica": {"politica"},
    "parecido": {"politica", "dudosa"},
    "no_politica": {"no_politica"},
}


def _grupo(nombre: str) -> str | None:
    for grupo in ("no_politica", "politica", "parecido"):
        if nombre.startswith(grupo + "_"):
            return grupo
    return None


def main(carpeta: Path) -> int:
    archivos = sorted(p for p in carpeta.glob("*.txt") if _grupo(p.name))
    if not archivos:
        print(f"No hay archivos politica_*, parecido_* ni no_politica_* en {carpeta}", file=sys.stderr)
        return 2

    separador = "=" * 97
    print(separador)
    print(f"  {'Archivo':<42} {'Palabras':>8} {'Temas':>6} {'Cobertura':>9} {'Voz':>4}  {'Decisión':<12} {'OK':>3}")
    print(separador)
    aciertos: dict[str, list[bool]] = {g: [] for g in ACEPTABLE}
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        grupo = _grupo(archivo.name)
        deteccion = detectar_politica(texto)
        ok = deteccion.resultado in ACEPTABLE[grupo]
        aciertos[grupo].append(ok)
        print(
            f"  {archivo.name[:42]:<42} {len(texto.split()):>8} "
            f"{len(deteccion.temas_encontrados):>3}/{len(TEMAS):<2} {deteccion.cobertura:>9.2f} {deteccion.voz_responsable:>4}  "
            f"{deteccion.resultado:<12} {'sí' if ok else 'NO':>3}"
        )
    print(separador)
    for grupo, lista in aciertos.items():
        if lista:
            print(f"  {grupo:<12}: {sum(lista)} de {len(lista)} correctos")
    print(separador)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
