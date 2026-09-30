import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight, FileSearch, ShieldAlert } from 'lucide-react'
import Navbar from '@/components/common/Navbar'
import IndicadorSemaforo from '@/components/analisis/IndicadorSemaforo'
import FormFiltrosHistorial from '@/components/historial/FormFiltrosHistorial'
import { useHistorial } from '@/hooks/useHistorial'
import type { AnalisisHistorialItem, FiltrosHistorial } from '@/types/analisis'

const hayFiltros = (filtros: FiltrosHistorial) =>
  Object.values(filtros).some((valor) => typeof valor === 'string' && valor.trim() !== '')

export default function Historial() {
  const { items, total, page, pageSize, filtros, isLoading, error, cargar } = useHistorial()

  useEffect(() => {
    cargar(1)
  }, [])

  const totalPaginas = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        <h1 className="text-xl font-bold text-gray-900 mb-6">Mis análisis</h1>

        <div className="mb-5">
          <FormFiltrosHistorial onAplicar={(nuevos) => cargar(1, nuevos)} deshabilitado={isLoading} />
        </div>

        {isLoading && <EstadoCargando />}
        {error && !isLoading && <EstadoError mensaje={error} />}

        {!isLoading && !error && items.length === 0 && (
          hayFiltros(filtros) ? <EstadoSinCoincidencias /> : <EstadoVacio />
        )}

        {!isLoading && !error && items.length > 0 && hayFiltros(filtros) && (
          <p className="text-xs text-gray-500 mb-3" aria-live="polite">
            {total === 1 ? '1 análisis coincide con los filtros.' : `${total} análisis coinciden con los filtros.`}
          </p>
        )}

        {!isLoading && !error && items.length > 0 && (
          <>
            <div className="space-y-3">
              {items.map((item) => (
                <TarjetaHistorial key={item.id_analisis} item={item} />
              ))}
            </div>

            <Paginacion
              page={page}
              totalPaginas={totalPaginas}
              onCambiarPagina={cargar}
              disabled={isLoading}
            />
          </>
        )}
      </main>
    </div>
  )
}

function TarjetaHistorial({ item }: { item: AnalisisHistorialItem }) {
  const fechaFormateada = new Date(item.fecha).toLocaleString('es-GT', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

  return (
    <Link
      to={`/resultados/${item.id_analisis}`}
      className="card flex items-center justify-between gap-3 hover:border-blue-300 hover:shadow-md transition-all"
    >
      <div className="min-w-0">
        <p className="text-xs text-gray-400">{fechaFormateada}</p>
        <p className="text-sm text-gray-700 mt-0.5 truncate">{item.comentario_breve}</p>
        <div className="mt-2">
          <IndicadorSemaforo nivel={item.nivel_riesgo_global} size="sm" />
        </div>
      </div>
      <div className="flex flex-col items-center justify-center w-12 h-12 rounded-full border-2 border-gray-100 bg-white shrink-0">
        <span className="text-sm font-black leading-none text-gray-700">{item.puntaje}</span>
        <span className="text-[10px] text-gray-400 leading-none">/100</span>
      </div>
    </Link>
  )
}

function Paginacion({
  page,
  totalPaginas,
  onCambiarPagina,
  disabled,
}: {
  page: number
  totalPaginas: number
  onCambiarPagina: (pagina: number) => void
  disabled: boolean
}) {
  return (
    <div className="flex items-center justify-between mt-5">
      <button
        onClick={() => onCambiarPagina(page - 1)}
        disabled={disabled || page <= 1}
        className="flex items-center gap-1 text-sm text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:text-blue-600"
      >
        <ChevronLeft size={16} />
        Anterior
      </button>
      <span className="text-xs text-gray-400">
        Página {page} de {totalPaginas}
      </span>
      <button
        onClick={() => onCambiarPagina(page + 1)}
        disabled={disabled || page >= totalPaginas}
        className="flex items-center gap-1 text-sm text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:text-blue-600"
      >
        Siguiente
        <ChevronRight size={16} />
      </button>
    </div>
  )
}

function EstadoCargando() {
  return (
    <div className="card text-center py-16 space-y-3">
      <div className="inline-flex w-12 h-12 rounded-full border-4 border-blue-200 border-t-blue-600
                      animate-spin mx-auto" />
      <p className="text-gray-500 text-sm">Cargando historial...</p>
    </div>
  )
}

function EstadoError({ mensaje }: { mensaje: string }) {
  return (
    <div className="card bg-red-50 border-red-200 text-center py-10 space-y-3">
      <ShieldAlert size={32} className="text-red-400 mx-auto" />
      <p className="text-red-700 text-sm">{mensaje}</p>
    </div>
  )
}

function EstadoSinCoincidencias() {
  return (
    <div className="card text-center py-12 space-y-2">
      <FileSearch size={32} className="text-gray-300 mx-auto" />
      <p className="text-gray-500 text-sm">No hay análisis que coincidan con los filtros.</p>
    </div>
  )
}

function EstadoVacio() {
  return (
    <div className="card text-center py-16 space-y-3">
      <FileSearch size={32} className="text-gray-300 mx-auto" />
      <p className="text-gray-500 text-sm">Aún no tienes análisis registrados.</p>
      <Link to="/analizar" className="inline-block btn-primary text-sm mt-2">
        Analizar una política
      </Link>
    </div>
  )
}
