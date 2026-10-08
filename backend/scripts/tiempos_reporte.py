#!/usr/bin/env python3
"""Estadísticas del tiempo de generación del reporte PDF (indicador de la Tabla 1).

Uso:
    docker compose exec backend python scripts/tiempos_reporte.py
    docker compose exec backend python scripts/tiempos_reporte.py --detalle

Lee los tiempos registrados en resultado.metadatos_reporte de cada análisis
(las últimas 10 generaciones de cada uno). No expone ninguna ruta de la API.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Necesario para que Python encuentre el paquete `app` desde scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.services.analisis_service import estadisticas_tiempos_reporte


def _linea(etiqueta: str, valor: float) -> str:
    return f"  {etiqueta:<24}: {valor:.4f} s"


async def main(detalle: bool) -> int:
    async with AsyncSessionLocal() as db:
        datos = await estadisticas_tiempos_reporte(db)

    resumen = datos["resumen"]
    separador = "=" * 52
    print(separador)
    print("  TIEMPO DE GENERACIÓN DEL REPORTE PDF")
    print(separador)
    print(f"  Análisis con reporte    : {datos['analisis_con_reporte']}")
    print(f"  Reportes generados      : {datos['total_generaciones']}")
    print(f"  Mediciones consideradas : {resumen['mediciones']}")
    if resumen["mediciones"]:
        print(_linea("Promedio", resumen["promedio"]))
        print(_linea("Mediana", resumen["mediana"]))
        print(_linea("Mínimo", resumen["minimo"]))
        print(_linea("Máximo", resumen["maximo"]))
        print(_linea("Percentil 95", resumen["p95"]))
    else:
        print("  Aún no se ha generado ningún reporte.")

    if detalle and datos["por_analisis"]:
        print(separador)
        print(f"  {'Análisis':>8}  {'Reportes':>8}  {'Último (s)':>10}  {'Promedio (s)':>12}")
        for fila in datos["por_analisis"]:
            print(
                f"  {fila['id']:>8}  {fila['total_generaciones']:>8}  "
                f"{fila['ultima_generacion_segundos']:>10.4f}  {fila['promedio']:>12.4f}"
            )
    print(separador)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detalle", action="store_true", help="Muestra el tiempo por análisis")
    sys.exit(asyncio.run(main(parser.parse_args().detalle)))
