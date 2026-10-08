import { useState } from 'react'
import { BookOpen, ChevronDown, ListChecks } from 'lucide-react'
import CitaNormativa from './CitaNormativa'
import IndicadorSemaforo from './IndicadorSemaforo'
import InsigniaNivel from './InsigniaNivel'
import AyudaGlosario from '@/components/glosario/AyudaGlosario'
import { porQueDelCriterio } from '@/data/criterios'
import type { Hallazgo, NivelRiesgo, SeccionAnalizada } from '@/types/analisis'

interface Props {
  seccion: SeccionAnalizada
  indice: number
  inicialmenteExpandida?: boolean
}

function nivelMaximo(seccion: SeccionAnalizada): NivelRiesgo {
  const niveles = seccion.hallazgos.map((h) => h.nivel)
  if (niveles.includes('alto')) return 'alto'
  if (niveles.includes('medio')) return 'medio'
  return 'bajo'
}

export default function TarjetaSeccion({ seccion, indice, inicialmenteExpandida = false }: Props) {
  const [expandida, setExpandida] = useState(inicialmenteExpandida)
  const nivel = nivelMaximo(seccion)
  const hayHallazgos = seccion.hallazgos.length > 0

  return (
    <div className="overflow-hidden rounded-2xl border border-borde bg-superficie">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-4 py-4 text-left transition-colors hover:bg-superficie-2"
        onClick={() => setExpandida((v) => !v)}
        aria-expanded={expandida}
      >
        <div className="flex min-w-0 items-start gap-3">
          <span className="mt-0.5 w-6 shrink-0 text-right text-sm font-bold text-texto-3">{indice}</span>
          <div className="min-w-0">
            <p className="text-base font-bold leading-snug text-texto">{seccion.titulo}</p>
            <p className="mt-0.5 truncate text-xs text-texto-2">{seccion.categoria_opp115}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          {hayHallazgos && <IndicadorSemaforo nivel={nivel} size="sm" />}
          <ChevronDown
            size={20}
            aria-hidden="true"
            className={`text-texto-3 transition-transform motion-reduce:transition-none ${expandida ? 'rotate-180' : ''}`}
          />
        </div>
      </button>

      {expandida && (
        <div className="space-y-4 border-t border-borde px-4 pb-4 pt-4">
          {hayHallazgos ? (
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-texto-2">
                Hallazgos ({seccion.hallazgos.length})
              </p>
              {seccion.hallazgos.map((hallazgo, i) => (
                <TarjetaHallazgo key={i} hallazgo={hallazgo} />
              ))}
            </div>
          ) : (
            <p className="text-sm italic text-texto-2">No se identificaron hallazgos en esta sección.</p>
          )}

          {seccion.texto_original && (
            <details className="rounded-xl bg-superficie-2 px-4 py-3">
              <summary className="cursor-pointer text-sm font-semibold text-texto-2">Ver el fragmento analizado</summary>
              <p className="mt-2 text-sm leading-relaxed text-texto-2">{seccion.texto_original}</p>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

function TarjetaHallazgo({ hallazgo }: { hallazgo: Hallazgo }) {
  const porQue = porQueDelCriterio(hallazgo.criterio)
  const fuentes = hallazgo.fuentes_normativas

  return (
    <article className="space-y-3 rounded-xl border border-borde p-4">
      <div className="flex flex-wrap items-center gap-2">
        <InsigniaNivel nivel={hallazgo.nivel} tipo={hallazgo.tipo} />
        {hallazgo.tipo_tratamiento && (
          <span className="inline-flex items-center gap-1">
            <span
              className="rounded-full bg-marca-suave px-2.5 py-1 text-xs font-semibold text-marca-suave-texto"
              title="Tipo de tratamiento de datos"
            >
              <span className="sr-only">Tipo de tratamiento: </span>
              {hallazgo.tipo_tratamiento}
            </span>
            <AyudaGlosario termino={hallazgo.tipo_tratamiento} />
          </span>
        )}
      </div>

      <p className="text-base leading-relaxed text-texto">{hallazgo.descripcion}</p>

      {porQue && (
        <p className="flex items-start gap-2 rounded-xl bg-superficie-2 px-3 py-2.5 text-sm text-texto">
          <ListChecks size={18} aria-hidden="true" className="mt-0.5 shrink-0 text-texto-2" />
          <span>
            <strong>Por qué: </strong>
            {porQue}
          </span>
        </p>
      )}

      {hallazgo.sin_respaldo && (
        <p className="flex items-center gap-1 text-xs text-texto-2">
          Sin respaldo en el corpus normativo: no se cita ninguna norma y no suma a la puntuación de riesgo.
          <AyudaGlosario termino="Sin respaldo en el corpus normativo" />
        </p>
      )}

      {fuentes.length > 0 && (
        <details className="border-t border-borde pt-3">
          <summary className="flex min-h-[32px] cursor-pointer items-center gap-2 text-sm font-semibold text-marca-texto">
            <BookOpen size={16} aria-hidden="true" />
            {fuentes.length === 1 ? 'Ver la norma que lo respalda' : `Ver las ${fuentes.length} normas que lo respaldan`}
          </summary>
          <div className="mt-2 space-y-2">
            {fuentes.map((fuente, j) => (
              <CitaNormativa key={j} fuente={fuente} />
            ))}
          </div>
        </details>
      )}
    </article>
  )
}
