import type { NivelRiesgo } from '@/types/analisis'

interface Props {
  nivel: NivelRiesgo
  size?: 'sm' | 'md' | 'lg'
  mostrarTexto?: boolean
}

const CONFIG: Record<NivelRiesgo, { dot: string; bg: string; text: string; label: string; descripcion: string }> = {
  bajo: {
    dot: 'bg-riesgo-bajo',
    bg: 'bg-riesgo-bajo/10 border-riesgo-bajo/30',
    text: 'text-riesgo-bajo',
    label: 'Riesgo Bajo',
    descripcion: 'Esta política muestra buenas prácticas de privacidad.',
  },
  medio: {
    dot: 'bg-riesgo-medio',
    bg: 'bg-riesgo-medio/10 border-riesgo-medio/30',
    text: 'text-riesgo-medio',
    label: 'Riesgo Medio',
    descripcion: 'Hay aspectos que merecen atención antes de aceptar.',
  },
  alto: {
    dot: 'bg-riesgo-alto',
    bg: 'bg-riesgo-alto/10 border-riesgo-alto/30',
    text: 'text-riesgo-alto',
    label: 'Riesgo Alto',
    descripcion: 'Esta política presenta cláusulas preocupantes para tu privacidad.',
  },
}

const DOT_SIZE: Record<string, string> = {
  sm: 'w-3 h-3',
  md: 'w-5 h-5',
  lg: 'w-7 h-7',
}

export default function IndicadorSemaforo({ nivel, size = 'md', mostrarTexto = false }: Props) {
  const cfg = CONFIG[nivel]

  if (mostrarTexto) {
    return (
      <div className={`inline-flex items-start gap-3 px-4 py-3 rounded-xl border ${cfg.bg}`}>
        <span
          className={`${DOT_SIZE[size]} ${cfg.dot} rounded-full shrink-0 mt-0.5 ring-4 ring-white`}
          aria-hidden="true"
        />
        <div>
          <p className={`font-semibold text-base ${cfg.text}`}>{cfg.label}</p>
          <p className={`text-sm mt-0.5 ${cfg.text} opacity-80`}>{cfg.descripcion}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <span
        className={`${DOT_SIZE[size]} ${cfg.dot} rounded-full ring-2 ring-white`}
        aria-hidden="true"
      />
      <span className={`font-medium text-sm ${cfg.text}`}>{cfg.label}</span>
    </div>
  )
}
