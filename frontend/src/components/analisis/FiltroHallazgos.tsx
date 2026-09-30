import type { Jurisdiccion, NivelRiesgo } from '@/types/analisis'
import { type FiltroHallazgos as Filtro, SIN_FILTRO, hayFiltroActivo } from '@/utils/filtrosHallazgos'
import { ETIQUETA_JURISDICCION } from '@/utils/jurisdiccion'

interface Props {
  filtro: Filtro
  onCambiar: (filtro: Filtro) => void
  visibles: number
  total: number
}

const NIVELES: NivelRiesgo[] = ['alto', 'medio', 'bajo']
const JURISDICCIONES: Jurisdiccion[] = ['guatemala', 'internacional', 'estandar_tecnico']

export default function FiltroHallazgos({ filtro, onCambiar, visibles, total }: Props) {
  return (
    <div role="group" aria-label="Filtrar hallazgos" className="card space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label htmlFor="filtro-hallazgos-nivel" className="text-sm font-medium text-gray-700">
            Nivel de riesgo
          </label>
          <select
            id="filtro-hallazgos-nivel"
            value={filtro.nivel}
            onChange={(e) => onCambiar({ ...filtro, nivel: e.target.value as Filtro['nivel'] })}
            className="input-field w-full mt-1"
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
          <label htmlFor="filtro-hallazgos-jurisdiccion" className="text-sm font-medium text-gray-700">
            Jurisdicción de la cita
          </label>
          <select
            id="filtro-hallazgos-jurisdiccion"
            value={filtro.jurisdiccion}
            onChange={(e) => onCambiar({ ...filtro, jurisdiccion: e.target.value as Filtro['jurisdiccion'] })}
            className="input-field w-full mt-1"
          >
            <option value="">Todas</option>
            {JURISDICCIONES.map((jurisdiccion) => (
              <option key={jurisdiccion} value={jurisdiccion}>
                {ETIQUETA_JURISDICCION[jurisdiccion]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-gray-500" aria-live="polite">
          Mostrando {visibles} de {total} hallazgos
        </p>
        {hayFiltroActivo(filtro) && (
          <button
            type="button"
            onClick={() => onCambiar(SIN_FILTRO)}
            className="text-xs font-medium text-blue-600 hover:underline"
          >
            Limpiar filtros
          </button>
        )}
      </div>
    </div>
  )
}
