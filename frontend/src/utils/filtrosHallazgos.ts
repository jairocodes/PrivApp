import type { Hallazgo, Jurisdiccion, NivelRiesgo, SeccionAnalizada } from '@/types/analisis'
import { inferirJurisdiccion } from '@/utils/jurisdiccion'

export interface FiltroHallazgos {
  nivel: NivelRiesgo | ''
  jurisdiccion: Jurisdiccion | ''
}

export const SIN_FILTRO: FiltroHallazgos = { nivel: '', jurisdiccion: '' }

export interface SeccionFiltrada {
  seccion: SeccionAnalizada
  /** Número de la sección en el análisis completo (no cambia al filtrar). */
  indice: number
}

export function hayFiltroActivo(filtro: FiltroHallazgos): boolean {
  return filtro.nivel !== '' || filtro.jurisdiccion !== ''
}

/** Un hallazgo coincide si tiene el nivel elegido y alguna cita de la jurisdicción elegida. */
export function hallazgoCoincide(hallazgo: Hallazgo, filtro: FiltroHallazgos): boolean {
  if (filtro.nivel && hallazgo.nivel !== filtro.nivel) return false
  if (filtro.jurisdiccion) {
    return hallazgo.fuentes_normativas.some(
      (fuente) => inferirJurisdiccion(fuente.documento) === filtro.jurisdiccion,
    )
  }
  return true
}

/**
 * Secciones con solo los hallazgos que coinciden. Sin filtro se devuelven todas
 * tal cual; con filtro se omiten las secciones que se quedan sin hallazgos.
 */
export function filtrarSecciones(secciones: SeccionAnalizada[], filtro: FiltroHallazgos): SeccionFiltrada[] {
  const numeradas = secciones.map((seccion, i) => ({ seccion, indice: i + 1 }))
  if (!hayFiltroActivo(filtro)) return numeradas
  return numeradas
    .map(({ seccion, indice }) => ({
      seccion: { ...seccion, hallazgos: seccion.hallazgos.filter((h) => hallazgoCoincide(h, filtro)) },
      indice,
    }))
    .filter(({ seccion }) => seccion.hallazgos.length > 0)
}

export function contarHallazgos(secciones: SeccionAnalizada[]): number {
  return secciones.reduce((total, seccion) => total + seccion.hallazgos.length, 0)
}
