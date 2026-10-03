#!/usr/bin/env python3
"""Mide la consistencia de los resultados al analizar varias veces la misma política.

Uso (con la pila local en marcha y una cuenta ya registrada):
    PRIVAPP_CORREO=... PRIVAPP_PASSWORD=... \\
        python scripts/medir_consistencia.py --archivo politica.txt --repeticiones 5

    # Medir la consistencia del modelo sin que el servidor reutilice resultados:
    python scripts/medir_consistencia.py --archivo politica.txt --sin-reutilizacion

    # Obtener el texto una sola vez desde una URL y guardarlo para reutilizarlo:
    python scripts/medir_consistencia.py --url-politica https://... --archivo politica.txt

Envía el mismo texto a POST /api/analisis/iniciar las veces indicadas, espera a que
cada análisis termine y compara los resultados: puntuación, nivel general,
hallazgos que cuentan para la puntuación, nivel de cada sección y recomendaciones.
El servidor reutiliza el resultado de un texto idéntico; con --sin-reutilizacion
cada análisis se elimina al terminar, para que el siguiente se calcule de nuevo.
Las credenciales se leen de variables de entorno para no dejarlas en el historial
de la terminal. Cada ejecución consume llamadas reales al modelo de lenguaje.
"""

import argparse
import itertools
import json
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import requests

# POST /api/analisis/iniciar admite 5 solicitudes por minuto.
_PAUSA_MINIMA_ENTRE_ANALISIS = 13.0
_INTERVALO_SONDEO = 3.0
_ESPERA_MAXIMA = 900.0


def _verificar(respuesta: requests.Response) -> requests.Response:
    """Como raise_for_status, pero muestra el mensaje de error de la API."""
    if respuesta.status_code >= 400:
        raise RuntimeError(f"{respuesta.request.method} {respuesta.url} -> {respuesta.status_code}: {respuesta.text[:300]}")
    return respuesta


def _iniciar_sesion(api: str, correo: str, password: str) -> requests.Session:
    sesion = requests.Session()
    respuesta = sesion.post(f"{api}/api/auth/login", json={"email": correo, "password": password}, timeout=30)
    _verificar(respuesta)
    sesion.headers["Authorization"] = f"Bearer {respuesta.json()['access_token']}"
    return sesion


def _texto_desde_url(sesion: requests.Session, api: str, url: str) -> str:
    respuesta = sesion.post(f"{api}/api/ingesta/url", json={"url": url}, timeout=120)
    _verificar(respuesta)
    return respuesta.json()["texto_procesado"]


def _ejecutar_analisis(sesion: requests.Session, api: str, texto: str) -> tuple[dict, float]:
    inicio = time.monotonic()
    respuesta = sesion.post(f"{api}/api/analisis/iniciar", json={"texto": texto}, timeout=60)
    _verificar(respuesta)
    id_analisis = respuesta.json()["id_analisis"]

    while True:
        if time.monotonic() - inicio > _ESPERA_MAXIMA:
            raise TimeoutError(f"El análisis {id_analisis} no terminó en {_ESPERA_MAXIMA:.0f} s")
        time.sleep(_INTERVALO_SONDEO)
        estado = sesion.get(f"{api}/api/analisis/{id_analisis}/estado", timeout=30)
        _verificar(estado)
        valor = estado.json()["estado"]
        if valor == "error":
            raise RuntimeError(f"El análisis {id_analisis} terminó con error")
        if valor == "completado":
            break

    resultado = sesion.get(f"{api}/api/analisis/{id_analisis}", timeout=30)
    _verificar(resultado)
    return resultado.json(), time.monotonic() - inicio


def _eliminar_analisis(sesion: requests.Session, api: str, id_analisis: str) -> None:
    _verificar(sesion.delete(f"{api}/api/analisis/{id_analisis}", timeout=30))


def _resumir_ejecucion(resultado: dict, segundos: float) -> dict:
    secciones = resultado["secciones_analizadas"]
    contados = [
        h for s in secciones if s.get("analizada", True)
        for h in s["hallazgos"] if not h.get("sin_respaldo", False)
    ]
    return {
        "id_analisis": resultado["id_analisis"],
        "segundos": round(segundos, 1),
        "puntaje": resultado["resumen_general"]["puntaje"],
        "nivel": resultado["resumen_general"]["nivel_riesgo_global"],
        "secciones": len(secciones),
        "secciones_sin_analizar": sum(1 for s in secciones if not s.get("analizada", True)),
        "hallazgos_contados": len(contados),
        "hallazgos_por_nivel": dict(Counter(h["nivel"] for h in contados)),
        "sin_respaldo": sum(1 for s in secciones for h in s["hallazgos"] if h.get("sin_respaldo", False)),
        # Niveles de cada sección, ordenados: permite comparar sección por sección.
        "niveles_por_seccion": [sorted(h["nivel"] for h in s["hallazgos"]) for s in secciones],
        "recomendaciones": resultado["recomendaciones"],
        "criterios": sorted(h.get("criterio") or "-" for s in secciones for h in s["hallazgos"]),
    }


def _similitud_jaccard(a: list[str], b: list[str]) -> float:
    conjunto_a = {r.strip().lower() for r in a}
    conjunto_b = {r.strip().lower() for r in b}
    if not conjunto_a and not conjunto_b:
        return 1.0
    return len(conjunto_a & conjunto_b) / len(conjunto_a | conjunto_b)


def _secciones_identicas(ejecuciones: list[dict]) -> tuple[int, int]:
    """Secciones cuyos niveles coinciden en todas las ejecuciones, sobre el total comparable."""
    por_ejecucion = [e["niveles_por_seccion"] for e in ejecuciones]
    if len({len(p) for p in por_ejecucion}) != 1:
        return 0, 0
    total = len(por_ejecucion[0])
    iguales = sum(1 for i in range(total) if all(p[i] == por_ejecucion[0][i] for p in por_ejecucion))
    return iguales, total


def _reporte(ejecuciones: list[dict]) -> dict:
    puntajes = [e["puntaje"] for e in ejecuciones]
    niveles = Counter(e["nivel"] for e in ejecuciones)
    similitudes = [
        _similitud_jaccard(a["recomendaciones"], b["recomendaciones"])
        for a, b in itertools.combinations(ejecuciones, 2)
    ]
    iguales, total = _secciones_identicas(ejecuciones)
    return {
        "ejecuciones": len(ejecuciones),
        "puntaje_promedio": round(statistics.mean(puntajes), 2),
        "puntaje_desviacion": round(statistics.stdev(puntajes), 2) if len(puntajes) > 1 else 0.0,
        "puntaje_minimo": min(puntajes),
        "puntaje_maximo": max(puntajes),
        "niveles": dict(niveles),
        "concordancia_nivel": round(niveles.most_common(1)[0][1] / len(ejecuciones), 2),
        "secciones_identicas": f"{iguales}/{total}" if total else "no comparable (distinto número de secciones)",
        "similitud_recomendaciones": round(statistics.mean(similitudes), 2) if similitudes else 1.0,
        "segundos_promedio": round(statistics.mean(e["segundos"] for e in ejecuciones), 1),
    }


def _imprimir(ejecuciones: list[dict], reporte: dict) -> None:
    separador = "=" * 72
    print(separador)
    print("  CONSISTENCIA DEL ANÁLISIS (mismo texto, varias ejecuciones)")
    print(separador)
    print(f"  {'N.º':>3}  {'Id':>6}  {'Punt.':>5}  {'Nivel':<6}  {'Contados':>8}  {'A/M/B':>8}  "
          f"{'Sin resp.':>9}  {'Sin anal.':>9}  {'Seg.':>6}")
    for n, e in enumerate(ejecuciones, start=1):
        por_nivel = e["hallazgos_por_nivel"]
        amb = f"{por_nivel.get('alto', 0)}/{por_nivel.get('medio', 0)}/{por_nivel.get('bajo', 0)}"
        print(f"  {n:>3}  {e['id_analisis']:>6}  {e['puntaje']:>5}  {e['nivel']:<6}  "
              f"{e['hallazgos_contados']:>8}  {amb:>8}  {e['sin_respaldo']:>9}  "
              f"{e['secciones_sin_analizar']:>9}  {e['segundos']:>6}")
    print(separador)
    print(f"  Puntuación: promedio {reporte['puntaje_promedio']}, desviación {reporte['puntaje_desviacion']}, "
          f"rango {reporte['puntaje_minimo']}–{reporte['puntaje_maximo']}")
    print(f"  Nivel general: {reporte['niveles']} (concordancia {reporte['concordancia_nivel']:.0%})")
    print(f"  Secciones con los mismos niveles en todas las ejecuciones: {reporte['secciones_identicas']}")
    print(f"  Similitud promedio de las recomendaciones (Jaccard): {reporte['similitud_recomendaciones']}")
    print(separador)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default="http://localhost:8000", help="URL base de la API")
    parser.add_argument("--archivo", type=Path, help="Archivo de texto con la política (UTF-8)")
    parser.add_argument("--url-politica", help="Obtiene el texto desde esta URL y lo guarda en --archivo")
    parser.add_argument("--repeticiones", type=int, default=5, help="0 solo obtiene el texto")
    parser.add_argument("--sin-reutilizacion", action="store_true",
                        help="Elimina cada análisis al terminar para que el siguiente se calcule de nuevo")
    parser.add_argument("--salida", type=Path, help="Guarda el detalle de cada ejecución en JSON")
    args = parser.parse_args()

    correo, password = os.environ.get("PRIVAPP_CORREO"), os.environ.get("PRIVAPP_PASSWORD")
    if not correo or not password:
        print("Define PRIVAPP_CORREO y PRIVAPP_PASSWORD con una cuenta registrada.", file=sys.stderr)
        return 2
    if args.archivo is None:
        print("Indica --archivo (y opcionalmente --url-politica para crearlo).", file=sys.stderr)
        return 2

    api = args.api.rstrip("/")
    sesion = _iniciar_sesion(api, correo, password)

    if args.url_politica:
        args.archivo.write_text(_texto_desde_url(sesion, api, args.url_politica), encoding="utf-8")
        print(f"Texto guardado en {args.archivo}.")
    if args.repeticiones < 1:
        return 0
    texto = args.archivo.read_text(encoding="utf-8")

    ejecuciones = []
    ultimo_inicio = 0.0
    for n in range(1, args.repeticiones + 1):
        espera = _PAUSA_MINIMA_ENTRE_ANALISIS - (time.monotonic() - ultimo_inicio)
        if espera > 0:
            time.sleep(espera)
        ultimo_inicio = time.monotonic()
        print(f"Ejecución {n} de {args.repeticiones}...", flush=True)
        resultado, segundos = _ejecutar_analisis(sesion, api, texto)
        ejecuciones.append(_resumir_ejecucion(resultado, segundos))
        if args.sin_reutilizacion:
            _eliminar_analisis(sesion, api, resultado["id_analisis"])

    reporte = _reporte(ejecuciones)
    _imprimir(ejecuciones, reporte)
    if args.salida:
        args.salida.write_text(
            json.dumps({"reporte": reporte, "ejecuciones": ejecuciones}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Detalle guardado en {args.salida}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
