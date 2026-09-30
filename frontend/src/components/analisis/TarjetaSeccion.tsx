import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import CitaNormativa from './CitaNormativa'
import IndicadorSemaforo from './IndicadorSemaforo'
import AyudaGlosario from '@/components/glosario/AyudaGlosario'
import type { NivelRiesgo, SeccionAnalizada } from '@/types/analisis'

interface Props {
  seccion: SeccionAnalizada
  indice: number
  inicialmenteExpandida?: boolean
}

const TIPO_ICONO: Record<string, string> = {
  riesgo: '⚠️',
  transparencia: '✅',
  neutral: 'ℹ️',
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
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm">
      {/* Cabecera — siempre visible */}
      <button
        className="w-full flex items-center justify-between gap-3 px-4 py-4 text-left hover:bg-gray-50 transition-colors"
        onClick={() => setExpandida((v) => !v)}
        aria-expanded={expandida}
      >
        <div className="flex items-start gap-3 min-w-0">
          <span className="text-xs font-bold text-gray-400 mt-0.5 shrink-0 w-5 text-right">
            {indice}
          </span>
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 text-base leading-snug">{seccion.titulo}</p>
            <p className="text-xs text-gray-500 mt-0.5 truncate">{seccion.categoria_opp115}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {hayHallazgos && <IndicadorSemaforo nivel={nivel} size="sm" />}
          <span className="text-gray-400">
            {expandida ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </span>
        </div>
      </button>

      {/* Contenido expandible */}
      {expandida && (
        <div className="px-4 pb-4 border-t border-gray-100 pt-3 space-y-4">
          {/* Texto original (extracto) */}
          {seccion.texto_original && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Fragmento analizado
              </p>
              <p className="text-sm text-gray-700 leading-relaxed line-clamp-4">
                {seccion.texto_original}
              </p>
            </div>
          )}

          {/* Hallazgos */}
          {hayHallazgos ? (
            <div className="space-y-3">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Hallazgos ({seccion.hallazgos.length})
              </p>
              {seccion.hallazgos.map((hallazgo, i) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3 space-y-2">
                  <div className="flex items-start gap-2">
                    <span className="shrink-0 text-base" role="img" aria-label={hallazgo.tipo}>
                      {TIPO_ICONO[hallazgo.tipo] ?? 'ℹ️'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <NivelChip nivel={hallazgo.nivel} />
                        <span className="text-xs text-gray-500 capitalize">{hallazgo.tipo}</span>
                        {hallazgo.tipo_tratamiento && (
                          <span className="inline-flex items-center gap-1">
                            <span
                              className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium"
                              title="Tipo de tratamiento de datos"
                            >
                              <span className="sr-only">Tipo de tratamiento: </span>
                              {hallazgo.tipo_tratamiento}
                            </span>
                            <AyudaGlosario termino={hallazgo.tipo_tratamiento} />
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-800 leading-relaxed">{hallazgo.descripcion}</p>
                    </div>
                  </div>

                  {hallazgo.sin_respaldo && (
                    <p className="text-xs text-gray-500 pl-7 flex items-center gap-1">
                      Sin respaldo en el corpus normativo: no se cita ninguna norma y no suma a la
                      puntuación de riesgo.
                      <AyudaGlosario termino="Sin respaldo en el corpus normativo" />
                    </p>
                  )}

                  {/* Fuentes normativas */}
                  {hallazgo.fuentes_normativas.length > 0 && (
                    <div className="space-y-2 mt-2 pl-7">
                      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                        Fuentes normativas
                      </p>
                      {hallazgo.fuentes_normativas.map((fn, j) => (
                        <CitaNormativa key={j} fuente={fn} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No se identificaron hallazgos en esta sección.</p>
          )}
        </div>
      )}
    </div>
  )
}

function NivelChip({ nivel }: { nivel: string }) {
  const cfg: Record<string, string> = {
    alto: 'bg-riesgo-alto/15 text-riesgo-alto',
    medio: 'bg-riesgo-medio/15 text-riesgo-medio',
    bajo: 'bg-riesgo-bajo/15 text-riesgo-bajo',
    neutral: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${cfg[nivel] ?? cfg.neutral}`}>
      {nivel}
    </span>
  )
}
