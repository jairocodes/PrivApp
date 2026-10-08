import { CircleAlert, CircleCheck, TriangleAlert } from 'lucide-react'
import Insignia from '@/components/common/Insignia'
import type { NivelRiesgo, TipoHallazgo } from '@/types/analisis'

const ICONOS = { alto: TriangleAlert, medio: CircleAlert, bajo: CircleCheck }
const ETIQUETAS: Record<NivelRiesgo, string> = { alto: 'Riesgo alto', medio: 'Riesgo medio', bajo: 'Riesgo bajo' }

interface Props {
  nivel: NivelRiesgo
  /** Un hallazgo de transparencia es una buena práctica, no un riesgo bajo. */
  tipo?: TipoHallazgo
  grande?: boolean
}

/** Nivel con icono y texto: nunca depende solo del color. */
export default function InsigniaNivel({ nivel, tipo = 'riesgo', grande = false }: Props) {
  const Icono = ICONOS[nivel]
  const etiqueta = tipo === 'transparencia' ? 'Buena práctica' : tipo === 'neutral' ? 'Informativo' : ETIQUETAS[nivel]
  return (
    <Insignia
      tono={tipo === 'neutral' ? 'neutro' : nivel}
      icono={<Icono size={grande ? 18 : 14} aria-hidden="true" />}
      className={grande ? 'px-4 py-2 text-base' : ''}
    >
      {etiqueta}
    </Insignia>
  )
}
