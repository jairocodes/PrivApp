import { BookOpen, History, House, ShieldPlus, UserRound } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface Seccion {
  ruta: string
  etiqueta: string
  icono: LucideIcon
  /** Otras rutas en las que esta sección se marca como la actual. */
  tambienEn?: string[]
}

// Destinos principales: las pestañas del celular (máximo 5) y la barra superior.
export const SECCIONES: Seccion[] = [
  { ruta: '/dashboard', etiqueta: 'Inicio', icono: House },
  { ruta: '/analizar', etiqueta: 'Analizar', icono: ShieldPlus, tambienEn: ['/resultados'] },
  { ruta: '/historial', etiqueta: 'Historial', icono: History },
  { ruta: '/glosario', etiqueta: 'Glosario', icono: BookOpen },
  { ruta: '/perfil', etiqueta: 'Perfil', icono: UserRound },
]

const coincide = (pathname: string, ruta: string) => pathname === ruta || pathname.startsWith(`${ruta}/`)

export function esSeccionActual(seccion: Seccion, pathname: string): boolean {
  return [seccion.ruta, ...(seccion.tambienEn ?? [])].some((ruta) => coincide(pathname, ruta))
}
