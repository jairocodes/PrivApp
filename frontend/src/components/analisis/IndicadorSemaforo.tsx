/**
 * Indicador visual de riesgo tipo semáforo. Implementación completa en Sprint 5.
 */
import type { NivelRiesgo } from '@/types/analisis'

interface Props {
  nivel: NivelRiesgo
}

const CONFIG: Record<NivelRiesgo, { color: string; label: string }> = {
  bajo: { color: 'bg-green-500', label: 'Riesgo Bajo' },
  medio: { color: 'bg-yellow-500', label: 'Riesgo Medio' },
  alto: { color: 'bg-red-500', label: 'Riesgo Alto' },
}

export default function IndicadorSemaforo({ nivel }: Props) {
  const { color, label } = CONFIG[nivel]
  return (
    <div className="flex items-center gap-2">
      <span className={`w-4 h-4 rounded-full ${color}`} aria-hidden="true" />
      <span className="font-medium text-sm">{label}</span>
    </div>
  )
}
