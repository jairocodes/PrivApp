import type { Jurisdiccion } from '@/types/analisis'

export const ETIQUETA_JURISDICCION: Record<Jurisdiccion, string> = {
  guatemala: 'Guatemala',
  internacional: 'Internacional',
  estandar_tecnico: 'Estándar técnico',
}

/**
 * Jurisdicción de una fuente citada, deducida del nombre del documento.
 * El reporte PDF (reportes_service._inferir_jurisdiccion) usa la misma
 * heurística para que ambos coincidan.
 */
export function inferirJurisdiccion(documento: string): Jurisdiccion {
  const d = documento.toLowerCase()
  if (d.includes('constituci') || d.includes('laip') || d.includes('guatemal')) return 'guatemala'
  if (d.includes('opp') || d.includes('tosdr')) return 'estandar_tecnico'
  return 'internacional'
}
