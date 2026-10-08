import type { Jurisdiccion, NivelRiesgo } from '@/types/analisis'
import { type FiltroHallazgos as Filtro, SIN_FILTRO, hayFiltroActivo } from '@/utils/filtrosHallazgos'
import { ETIQUETA_JURISDICCION } from '@/utils/jurisdiccion'

interface Props {
  filtro: Filtro
  onCambiar: (filtro: Filtro) => void
  visibles: number
  total: number
  /** Tipos de tratamiento presentes en el análisis; sin ellos no se ofrece ese filtro. */
  tratamientos?: string[]
}

const NIVELES: NivelRiesgo[] = ['alto', 'medio', 'bajo']
const JURISDICCIONES: Jurisdiccion[] = ['guatemala', 'internacional', 'estandar_tecnico']
const ETIQUETA = 'text-sm font-semibold text-texto'

export default function FiltroHallazgos({ filtro, onCambiar, visibles, total, tratamientos = [] }: Props) {
  return (
    <div role="group" aria-label="Filtrar hallazgos" className="card space-y-3 p-4">
      <div className={`grid grid-cols-1 gap-3 ${tratamientos.length ? 'sm:grid-cols-3' : 'sm:grid-cols-2'}`}>
        <div>
          <label htmlFor="filtro-hallazgos-nivel" className={ETIQUETA}>
            Nivel de riesgo
          </label>
          <select
            id="filtro-hallazgos-nivel"
            value={filtro.nivel}
            onChange={(e) => onCambiar({ ...filtro, nivel: e.target.value as Filtro['nivel'] })}
            className="input-field mt-1.5"
          >
            <option value="">Todos</option>
            {NIVELES.map((nivel) => (
              <option key={nivel} value={nivel}>
                {nivel.charAt(0).toUpperCase() + nivel.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filtro-hallazgos-jurisdiccion" className={ETIQUETA}>
            Jurisdicción de la cita
          </label>
          <select
            id="filtro-hallazgos-jurisdiccion"
            value={filtro.jurisdiccion}
            onChange={(e) => onCambiar({ ...filtro, jurisdiccion: e.target.value as Filtro['jurisdiccion'] })}
            className="input-field mt-1.5"
          >
            <option value="">Todas</option>
            {JURISDICCIONES.map((jurisdiccion) => (
              <option key={jurisdiccion} value={jurisdiccion}>
                {ETIQUETA_JURISDICCION[jurisdiccion]}
              </option>
            ))}
          </select>
        </div>
        {tratamientos.length > 0 && (
          <div>
            <label htmlFor="filtro-hallazgos-tratamiento" className={ETIQUETA}>
              Tipo de tratamiento
            </label>
            <select
              id="filtro-hallazgos-tratamiento"
              value={filtro.tratamiento ?? ''}
              onChange={(e) => onCambiar({ ...filtro, tratamiento: e.target.value })}
              className="input-field mt-1.5"
            >
              <option value="">Todos</option>
              {tratamientos.map((tratamiento) => (
                <option key={tratamiento} value={tratamiento}>
                  {tratamiento}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-texto-2" aria-live="polite">
          Mostrando {visibles} de {total} hallazgos
        </p>
        {hayFiltroActivo(filtro) && (
          <button
            type="button"
            onClick={() => onCambiar(SIN_FILTRO)}
            className="inline-flex min-h-[44px] items-center px-2 text-sm font-semibold text-marca-texto hover:underline"
          >
            Limpiar filtros
          </button>
        )}
      </div>
    </div>
  )
}
