import AyudaGlosario from '@/components/glosario/AyudaGlosario'
import type { FuenteNormativa, Jurisdiccion } from '@/types/analisis'
import { jurisdiccionDeFuente } from '@/utils/jurisdiccion'

interface Props {
  fuente: FuenteNormativa
  jurisdiccion?: Jurisdiccion | string
}

const BADGE: Record<string, { bg: string; text: string; label: string }> = {
  guatemala: {
    bg: 'bg-marca-suave',
    text: 'text-marca-texto',
    label: 'Guatemala',
  },
  internacional: {
    bg: 'bg-juri-fondo',
    text: 'text-juri-texto',
    label: 'Internacional',
  },
  estandar_tecnico: {
    bg: 'bg-superficie-2',
    text: 'text-texto-2',
    label: 'Estándar técnico',
  },
}

export default function CitaNormativa({ fuente, jurisdiccion }: Props) {
  const jur = jurisdiccion ?? jurisdiccionDeFuente(fuente)
  const badge = BADGE[jur] ?? BADGE.internacional

  return (
    <div className="rounded-lg border border-borde bg-superficie-2 p-3 text-sm space-y-1">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.bg} ${badge.text}`}>
          {badge.label}
        </span>
        <span className="font-medium text-texto text-xs">{fuente.documento}</span>
        {fuente.referencia && (
          <span className="text-texto-2 text-xs">— {fuente.referencia}</span>
        )}
      </div>
      {fuente.fragmento_relevante && (
        <blockquote className="text-texto-2 text-xs italic border-l-2 border-borde-fuerte pl-2 leading-relaxed">
          {fuente.fragmento_relevante}
        </blockquote>
      )}
      {jur === 'internacional' && (
        <p className="text-xs text-texto-3 flex items-center gap-1">
          Referencia internacional — buena práctica, no ley vigente en Guatemala.
          <AyudaGlosario termino="Referencia internacional" />
        </p>
      )}
    </div>
  )
}
