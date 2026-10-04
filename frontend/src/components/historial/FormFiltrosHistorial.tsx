import { useState } from 'react'
import { Search } from 'lucide-react'
import type { FiltrosHistorial, NivelRiesgo } from '@/types/analisis'

interface Props {
  onAplicar: (filtros: FiltrosHistorial) => void
  deshabilitado?: boolean
}

const VACIO: FiltrosHistorial = { texto: '', nivel: '', desde: '', hasta: '' }

export default function FormFiltrosHistorial({ onAplicar, deshabilitado = false }: Props) {
  const [valores, setValores] = useState<FiltrosHistorial>(VACIO)
  const [error, setError] = useState<string | null>(null)

  const cambiar = (campo: keyof FiltrosHistorial) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    setValores({ ...valores, [campo]: e.target.value })
    setError(null)
  }

  const aplicar = (e: React.FormEvent) => {
    e.preventDefault()
    if (valores.desde && valores.hasta && valores.desde > valores.hasta) {
      setError('La fecha inicial no puede ser posterior a la fecha final.')
      return
    }
    onAplicar(valores)
  }

  const limpiar = () => {
    setValores(VACIO)
    setError(null)
    onAplicar(VACIO)
  }

  return (
    <form onSubmit={aplicar} noValidate role="search" aria-label="Filtros del historial" className="card space-y-3">
      <div>
        <label htmlFor="filtro-texto" className="text-sm font-medium text-texto-2">
          Buscar
        </label>
        <input
          id="filtro-texto"
          type="search"
          value={valores.texto}
          onChange={cambiar('texto')}
          placeholder="Texto de la política o del resumen"
          maxLength={100}
          className="input-field w-full mt-1"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label htmlFor="filtro-nivel" className="text-sm font-medium text-texto-2">
            Nivel de riesgo
          </label>
          <select
            id="filtro-nivel"
            value={valores.nivel}
            onChange={cambiar('nivel')}
            className="input-field w-full mt-1"
          >
            <option value="">Todos</option>
            {(['bajo', 'medio', 'alto'] as NivelRiesgo[]).map((nivel) => (
              <option key={nivel} value={nivel}>
                {nivel.charAt(0).toUpperCase() + nivel.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filtro-desde" className="text-sm font-medium text-texto-2">
            Desde
          </label>
          <input
            id="filtro-desde"
            type="date"
            value={valores.desde}
            max={valores.hasta || undefined}
            onChange={cambiar('desde')}
            className="input-field w-full mt-1"
          />
        </div>
        <div>
          <label htmlFor="filtro-hasta" className="text-sm font-medium text-texto-2">
            Hasta
          </label>
          <input
            id="filtro-hasta"
            type="date"
            value={valores.hasta}
            min={valores.desde || undefined}
            onChange={cambiar('hasta')}
            className="input-field w-full mt-1"
          />
        </div>
      </div>

      {error && (
        <p role="alert" className="text-sm text-riesgo-alto">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="submit"
          disabled={deshabilitado}
          className="btn-primary inline-flex items-center gap-1 text-sm"
        >
          <Search size={16} aria-hidden="true" />
          Aplicar filtros
        </button>
        <button type="button" onClick={limpiar} disabled={deshabilitado} className="btn-secondary text-sm">
          Limpiar filtros
        </button>
      </div>
    </form>
  )
}
