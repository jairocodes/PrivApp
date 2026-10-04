import { ArrowRight, CircleHelp, Clock, Database, Lock, RefreshCw, Share2, Target, UserCheck } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Hallazgo } from '@/types/analisis'
import { describirConteo, riesgosPorTratamiento } from '@/utils/resumenResultados'

interface Props {
  hallazgos: Hallazgo[]
  /** Muestra en la lista solo los hallazgos de ese tipo de tratamiento. */
  onVerTratamiento: (tratamiento: string) => void
  onVerTodos: () => void
}

const ICONOS: Record<string, LucideIcon> = {
  'Recopilación de datos personales': Database,
  'Uso y finalidad de los datos': Target,
  'Transferencia de datos a terceros': Share2,
  'Tiempo de conservación de los datos': Clock,
  'Seguridad de los datos': Lock,
  'Derechos del usuario sobre sus datos': UserCheck,
  'Cambios en la política': RefreshCw,
}

const FICHA =
  'flex min-h-[128px] flex-col gap-2.5 rounded-2xl border border-borde bg-superficie p-4 text-left transition-colors hover:border-marca-borde'

/** Riesgos agrupados por tipo de tratamiento de datos (RN-08), como fichas. */
export default function ResumenTratamiento({ hallazgos, onVerTratamiento, onVerTodos }: Props) {
  const grupos = riesgosPorTratamiento(hallazgos)
  if (grupos.length === 0) return null

  return (
    <section aria-labelledby="titulo-tratamiento" className="space-y-3">
      <h2 id="titulo-tratamiento" className="px-1 text-lg font-bold text-texto">
        Qué hace con tus datos
      </h2>
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {grupos.map(({ tratamiento, conteo }) => {
          const Icono = ICONOS[tratamiento] ?? CircleHelp
          return (
            <li key={tratamiento}>
              <button type="button" onClick={() => onVerTratamiento(tratamiento)} className={`${FICHA} w-full`}>
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-marca-suave text-marca-texto">
                  <Icono size={22} aria-hidden="true" />
                </span>
                <span className="text-sm font-bold leading-snug text-texto">{tratamiento}</span>
                <span className={`text-xs font-semibold ${conteo.alto ? 'text-riesgo-alto' : 'text-riesgo-medio'}`}>
                  {describirConteo(conteo)}
                </span>
              </button>
            </li>
          )
        })}
        <li>
          <button
            type="button"
            onClick={onVerTodos}
            className="flex min-h-[128px] w-full flex-col justify-between gap-2 rounded-2xl bg-marca-suave p-4 text-left text-marca-suave-texto"
          >
            <span className="text-sm font-bold leading-snug">Ver todos los hallazgos, sección por sección</span>
            <ArrowRight size={20} aria-hidden="true" />
          </button>
        </li>
      </ul>
    </section>
  )
}
