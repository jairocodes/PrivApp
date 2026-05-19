import type { FuenteNormativa, Jurisdiccion } from '@/types/analisis'

interface Props {
  fuente: FuenteNormativa
  jurisdiccion?: Jurisdiccion | string
}

const BADGE: Record<string, { bg: string; text: string; label: string }> = {
  guatemala: {
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    label: 'Guatemala',
  },
  internacional: {
    bg: 'bg-purple-100',
    text: 'text-purple-700',
    label: 'Internacional',
  },
  estandar_tecnico: {
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    label: 'Estándar técnico',
  },
}

function inferirJurisdiccion(documento: string): string {
  const d = documento.toLowerCase()
  if (d.includes('constituci') || d.includes('laip') || d.includes('guatemal')) return 'guatemala'
  if (d.includes('opp') || d.includes('tosdr')) return 'estandar_tecnico'
  return 'internacional'
}

export default function CitaNormativa({ fuente, jurisdiccion }: Props) {
  const jur = jurisdiccion ?? inferirJurisdiccion(fuente.documento)
  const badge = BADGE[jur] ?? BADGE.internacional

  return (
    <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm space-y-1">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.bg} ${badge.text}`}>
          {badge.label}
        </span>
        <span className="font-medium text-gray-800 text-xs">{fuente.documento}</span>
        {fuente.referencia && (
          <span className="text-gray-500 text-xs">— {fuente.referencia}</span>
        )}
      </div>
      {fuente.fragmento_relevante && (
        <blockquote className="text-gray-600 text-xs italic border-l-2 border-gray-300 pl-2 leading-relaxed">
          {fuente.fragmento_relevante}
        </blockquote>
      )}
      {jur === 'internacional' && (
        <p className="text-xs text-gray-400">
          Referencia internacional — buena práctica, no ley vigente en Guatemala.
        </p>
      )}
    </div>
  )
}
