import { Lightbulb } from 'lucide-react'
import AyudaGlosario from '@/components/glosario/AyudaGlosario'

interface Props {
  recomendaciones: string[]
}

/** Recomendaciones como tarjetas de acción numeradas, de la más importante a la menos. */
export default function ListaRecomendaciones({ recomendaciones }: Props) {
  if (recomendaciones.length === 0) return null

  return (
    <section aria-labelledby="titulo-recomendaciones" className="space-y-3">
      <div className="flex items-center gap-3 px-1">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-riesgo-medio/10 text-riesgo-medio">
          <Lightbulb size={20} aria-hidden="true" />
        </span>
        <h2 id="titulo-recomendaciones" className="text-lg font-bold text-texto">
          Qué puedes hacer
        </h2>
        <AyudaGlosario termino="Recomendación" />
      </div>
      <ol className="space-y-3">
        {recomendaciones.map((rec, i) => (
          <li key={i} className="flex items-start gap-3 rounded-2xl border border-borde bg-superficie p-4">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-marca text-sm font-extrabold text-white">
              {i + 1}
            </span>
            <span className="text-base leading-relaxed text-texto">{rec}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}
