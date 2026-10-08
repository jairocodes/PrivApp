import type { ReactNode } from 'react'

export type TonoInsignia = 'alto' | 'medio' | 'bajo' | 'marca' | 'neutro' | 'juri'

const TONOS: Record<TonoInsignia, string> = {
  alto: 'bg-riesgo-alto/10 text-riesgo-alto',
  medio: 'bg-riesgo-medio/10 text-riesgo-medio',
  bajo: 'bg-riesgo-bajo/10 text-riesgo-bajo',
  marca: 'bg-marca-suave text-marca-suave-texto',
  neutro: 'bg-superficie-2 text-texto-2',
  juri: 'bg-juri-fondo text-juri-texto',
}

interface Props {
  tono: TonoInsignia
  children: ReactNode
  /** Icono decorativo antes del texto (el texto siempre dice lo que significa). */
  icono?: ReactNode
  className?: string
  title?: string
}

/** Etiqueta breve (nivel, tipo de tratamiento, jurisdicción, estado). */
export default function Insignia({ tono, children, icono, className = '', title }: Props) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${TONOS[tono]} ${className}`}
    >
      {icono}
      {children}
    </span>
  )
}
