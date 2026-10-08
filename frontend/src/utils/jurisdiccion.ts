import type { FuenteNormativa, Jurisdiccion } from '@/types/analisis'

export const ETIQUETA_JURISDICCION: Record<Jurisdiccion, string> = {
  guatemala: 'Guatemala',
  internacional: 'Internacional',
  estandar_tecnico: 'Estándar técnico',
}

const CLAVES_GUATEMALA = ['constituci', 'laip', 'guatemal', 'decreto 57', '57-2008', 'acceso a la informaci']
const CLAVES_ESTANDAR = ['opp', 'tosdr', 'tos;dr', 'tos dr']

/**
 * Jurisdicción de una fuente citada, deducida del nombre del documento.
 * El reporte PDF (reportes_service._inferir_jurisdiccion) usa las mismas
 * claves para que ambos coincidan.
 */
export function inferirJurisdiccion(documento: string): Jurisdiccion {
  const d = documento.toLowerCase()
  if (CLAVES_GUATEMALA.some((clave) => d.includes(clave))) return 'guatemala'
  if (CLAVES_ESTANDAR.some((clave) => d.includes(clave))) return 'estandar_tecnico'
  return 'internacional'
}

/**
 * Jurisdicción de una cita: la que guardó el servidor desde el fragmento del
 * corpus o, en los análisis antiguos, la deducida del nombre del documento.
 */
export function jurisdiccionDeFuente(fuente: FuenteNormativa): Jurisdiccion {
  return fuente.jurisdiccion ?? inferirJurisdiccion(fuente.documento)
}
