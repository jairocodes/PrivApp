import { useState } from 'react'
import { Search } from 'lucide-react'
import Aviso from '@/components/common/Aviso'
import type { FiltrosHistorial, NivelRiesgo } from '@/types/analisis'

interface Props {
  onAplicar: (filtros: FiltrosHistorial) => void
  deshabilitado?: boolean
}

const VACIO: FiltrosHistorial = { texto: '', nivel: '', desde: '', hasta: '' }
const ETIQUETA = 'text-sm font-semibold text-texto'

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
    <form onSubmit={aplicar} noValidate role="search" aria-label="Filtros del historial" className="card space-y-4 p-4">
      <div>
        <label htmlFor="filtro-texto" className="sr-only">
          Buscar
        </label>
        <div className="relative">
          <Search
            size={20}
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-texto-2"
          />
          <input
            id="filtro-texto"
            type="search"
            value={valores.texto}
            onChange={cambiar('texto')}
            placeholder="Buscar en la política o en el resumen"
            maxLength={100}
            className="input-field pl-10"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <label htmlFor="filtro-nivel" className={ETIQUETA}>
            Nivel de riesgo
          </label>
          <select id="filtro-nivel" value={valores.nivel} onChange={cambiar('nivel')} className="input-field mt-1.5">
            <option value="">Todos</option>
            {(['bajo', 'medio', 'alto'] as NivelRiesgo[]).map((nivel) => (
              <option key={nivel} value={nivel}>
                {nivel.charAt(0).toUpperCase() + nivel.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filtro-desde" className={ETIQUETA}>
            Desde
          </label>
          <input
            id="filtro-desde"
            type="date"
            value={valores.desde}
            max={valores.hasta || undefined}
            onChange={cambiar('desde')}
            className="input-field mt-1.5"
          />
        </div>
        <div>
          <label htmlFor="filtro-hasta" className={ETIQUETA}>
            Hasta
          </label>
          <input
            id="filtro-hasta"
            type="date"
            value={valores.hasta}
            min={valores.desde || undefined}
            onChange={cambiar('hasta')}
            className="input-field mt-1.5"
          />
        </div>
      </div>

      {error && <Aviso tipo="error">{error}</Aviso>}

      <div className="grid grid-cols-2 gap-2 sm:flex">
        <button type="submit" disabled={deshabilitado} className="btn-primary text-sm">
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
