import type { Hallazgo, NivelRiesgo, ResumenGeneral, SeccionAnalizada } from '@/types/analisis'

export type ConteoNiveles = Record<NivelRiesgo, number>

/** Hallazgos que cuentan para el nivel y la puntuación (RN-05, RN-06): de
 *  secciones analizadas y con respaldo en el corpus. */
export function hallazgosQueCuentan(secciones: SeccionAnalizada[]): Hallazgo[] {
  return secciones
    .filter((s) => s.analizada !== false)
    .flatMap((s) => s.hallazgos)
    .filter((h) => !h.sin_respaldo)
}

export function contarPorNivel(hallazgos: Hallazgo[]): ConteoNiveles {
  const conteo: ConteoNiveles = { alto: 0, medio: 0, bajo: 0 }
  for (const h of hallazgos) conteo[h.nivel] += 1
  return conteo
}

export function hallazgosSinRespaldo(secciones: SeccionAnalizada[]): number {
  return secciones.flatMap((s) => s.hallazgos).filter((h) => h.sin_respaldo).length
}

/** Por qué el nivel general es el que es, con la misma regla del servidor (RN-05). */
export function explicarNivel(resumen: ResumenGeneral, conteo: ConteoNiveles): string {
  const { nivel_riesgo_global: nivel, puntaje } = resumen
  if (nivel === 'alto') {
    return conteo.alto >= 2
      ? `El nivel es alto porque hay ${conteo.alto} cláusulas de riesgo alto: con 2 o más, el nivel general es alto.`
      : `El nivel es alto porque la puntuación (${puntaje}) es de 75 o más.`
  }
  if (nivel === 'medio') {
    return conteo.medio >= 2
      ? `El nivel es medio porque hay ${conteo.medio} cláusulas de riesgo medio: con 2 o más, el nivel general es al menos medio.`
      : `El nivel es medio porque la puntuación (${puntaje}) es de 25 o más.`
  }
  return 'El nivel es bajo porque la política no tiene suficientes cláusulas de riesgo alto o medio.'
}

export interface ResumenTratamiento {
  tratamiento: string
  conteo: ConteoNiveles
  total: number
}

/** Hallazgos de riesgo agrupados por tipo de tratamiento de datos (RN-08), del
 *  que tiene más riesgos altos al que menos. */
export function riesgosPorTratamiento(hallazgos: Hallazgo[]): ResumenTratamiento[] {
  const grupos = new Map<string, ConteoNiveles>()
  for (const h of hallazgos) {
    if (h.tipo !== 'riesgo' || !h.tipo_tratamiento) continue
    const conteo = grupos.get(h.tipo_tratamiento) ?? { alto: 0, medio: 0, bajo: 0 }
    conteo[h.nivel] += 1
    grupos.set(h.tipo_tratamiento, conteo)
  }
  return [...grupos.entries()]
    .map(([tratamiento, conteo]) => ({ tratamiento, conteo, total: conteo.alto + conteo.medio + conteo.bajo }))
    .sort((a, b) => b.conteo.alto - a.conteo.alto || b.total - a.total || a.tratamiento.localeCompare(b.tratamiento))
}

/** "6 altos · 2 medios" */
export function describirConteo(conteo: ConteoNiveles): string {
  const partes: string[] = []
  if (conteo.alto) partes.push(`${conteo.alto} ${conteo.alto === 1 ? 'alto' : 'altos'}`)
  if (conteo.medio) partes.push(`${conteo.medio} ${conteo.medio === 1 ? 'medio' : 'medios'}`)
  if (conteo.bajo) partes.push(`${conteo.bajo} ${conteo.bajo === 1 ? 'bajo' : 'bajos'}`)
  return partes.join(' · ')
}
