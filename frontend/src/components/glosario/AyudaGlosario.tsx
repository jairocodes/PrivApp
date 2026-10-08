import { useId, useState } from 'react'
import { HelpCircle } from 'lucide-react'
import { entradaPorTermino } from '@/data/glosario'

interface Props {
  termino: string
}

/** Botón junto a un término técnico que muestra su definición del glosario. */
export default function AyudaGlosario({ termino }: Props) {
  const [abierta, setAbierta] = useState(false)
  const idPanel = useId()
  const entrada = entradaPorTermino(termino)
  if (!entrada) return null

  return (
    <span className="relative inline-flex align-middle">
      <button
        type="button"
        onClick={() => setAbierta((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') setAbierta(false)
        }}
        aria-expanded={abierta}
        aria-controls={idPanel}
        aria-label={`Qué significa «${entrada.termino}»`}
        className="text-texto-3 hover:text-marca-texto transition-colors"
      >
        <HelpCircle size={14} aria-hidden="true" />
      </button>
      {abierta && (
        <span
          id={idPanel}
          role="note"
          className="absolute left-0 top-5 z-20 w-64 rounded-lg border border-borde bg-superficie p-3
                     text-left text-xs font-normal normal-case text-texto-2 shadow-lg"
        >
          <span className="block font-semibold text-texto mb-1">{entrada.termino}</span>
          <span className="block leading-relaxed">{entrada.definicion}</span>
          {/* Enlace normal (no del router) para que el navegador baje hasta el término. */}
          <a href={`/glosario#${entrada.id}`} className="mt-2 inline-block text-marca-texto hover:underline">
            Ver en el glosario
          </a>
        </span>
      )}
    </span>
  )
}
