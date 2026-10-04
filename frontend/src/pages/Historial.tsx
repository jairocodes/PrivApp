import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FileSearch, Trash2 } from 'lucide-react'
import { analisisApi } from '@/api/analisis'
import Aviso from '@/components/common/Aviso'
import Cargando from '@/components/common/Cargando'
import DialogoConfirmacion from '@/components/common/DialogoConfirmacion'
import EstadoVacio from '@/components/common/EstadoVacio'
import Paginacion from '@/components/common/Paginacion'
import IndicadorSemaforo from '@/components/analisis/IndicadorSemaforo'
import FormFiltrosHistorial from '@/components/historial/FormFiltrosHistorial'
import { useHistorial } from '@/hooks/useHistorial'
import type { AnalisisHistorialItem, FiltrosHistorial } from '@/types/analisis'
import { MENSAJE_ELIMINAR_ANALISIS, detalleDeError } from '@/utils/errores'

const hayFiltros = (filtros: FiltrosHistorial) =>
  Object.values(filtros).some((valor) => typeof valor === 'string' && valor.trim() !== '')

export default function Historial() {
  const { items, total, page, pageSize, filtros, isLoading, error, cargar } = useHistorial()

  useEffect(() => {
    cargar(1)
  }, [])

  const totalPaginas = Math.max(1, Math.ceil(total / pageSize))
  // Aviso que deja otra pantalla al volver (p. ej. tras eliminar desde el detalle).
  const mensaje = (useLocation().state as { mensaje?: string } | null)?.mensaje

  const [porEliminar, setPorEliminar] = useState<AnalisisHistorialItem | null>(null)
  const [eliminando, setEliminando] = useState(false)
  const [errorEliminar, setErrorEliminar] = useState<string | null>(null)

  const confirmarEliminacion = async () => {
    if (!porEliminar) return
    setEliminando(true)
    setErrorEliminar(null)
    try {
      await analisisApi.eliminar(porEliminar.id_analisis)
      setPorEliminar(null)
      // Si era el último de la página, se vuelve a la anterior.
      await cargar(items.length === 1 && page > 1 ? page - 1 : page)
    } catch (err: unknown) {
      setErrorEliminar(detalleDeError(err, 'No fue posible eliminar el análisis. Intenta nuevamente.'))
    } finally {
      setEliminando(false)
    }
  }

  return (
    <>

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        <h1 className="text-xl font-bold text-texto mb-6">Mis análisis</h1>

        {mensaje && (
          <Aviso tipo="exito" className="mb-4">
            {mensaje}
          </Aviso>
        )}

        <div className="mb-5">
          <FormFiltrosHistorial onAplicar={(nuevos) => cargar(1, nuevos)} deshabilitado={isLoading} />
        </div>

        {isLoading && <Cargando mensaje="Cargando historial..." />}
        {error && !isLoading && <Aviso tipo="error">{error}</Aviso>}

        {!isLoading && !error && items.length === 0 && (
          hayFiltros(filtros) ? (
            <EstadoVacio icono={FileSearch} mensaje="No hay análisis que coincidan con los filtros." />
          ) : (
            <EstadoVacio
              icono={FileSearch}
              mensaje="Aún no tienes análisis registrados."
              accion={<Link to="/analizar" className="btn-primary text-sm">Analizar una política</Link>}
            />
          )
        )}

        {!isLoading && !error && items.length > 0 && hayFiltros(filtros) && (
          <p className="text-xs text-texto-2 mb-3" aria-live="polite">
            {total === 1 ? '1 análisis coincide con los filtros.' : `${total} análisis coinciden con los filtros.`}
          </p>
        )}

        {!isLoading && !error && items.length > 0 && (
          <>
            <div className="space-y-3">
              {items.map((item) => (
                <TarjetaHistorial
                  key={item.id_analisis}
                  item={item}
                  onEliminar={() => {
                    setErrorEliminar(null)
                    setPorEliminar(item)
                  }}
                />
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

      <DialogoConfirmacion
        abierto={porEliminar !== null}
        titulo="¿Eliminar este análisis?"
        mensaje={MENSAJE_ELIMINAR_ANALISIS}
        textoConfirmar="Eliminar"
        procesando={eliminando}
        error={errorEliminar}
        onConfirmar={confirmarEliminacion}
        onCancelar={() => setPorEliminar(null)}
      />
    </>
  )
}

function TarjetaHistorial({ item, onEliminar }: { item: AnalisisHistorialItem; onEliminar: () => void }) {
  const fechaFormateada = new Date(item.fecha).toLocaleString('es-GT', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

  return (
    <div className="card flex items-center gap-3 hover:border-marca-borde hover:shadow-md transition-all">
      <Link
        to={`/resultados/${item.id_analisis}`}
        className="flex flex-1 min-w-0 items-center justify-between gap-3"
      >
        <div className="min-w-0">
          <p className="text-xs text-texto-3">{fechaFormateada}</p>
          <p className="text-sm text-texto-2 mt-0.5 truncate">{item.comentario_breve}</p>
          <div className="mt-2">
            <IndicadorSemaforo nivel={item.nivel_riesgo_global} size="sm" />
          </div>
        </div>
        <div className="flex flex-col items-center justify-center w-12 h-12 rounded-full border-2 border-borde bg-superficie shrink-0">
          <span className="text-sm font-black leading-none text-texto-2">{item.puntaje}</span>
          <span className="text-[10px] text-texto-3 leading-none">/100</span>
        </div>
      </Link>
      <button
        type="button"
        onClick={onEliminar}
        aria-label={`Eliminar el análisis del ${fechaFormateada}`}
        className="p-2 rounded-lg text-texto-3 hover:text-riesgo-alto hover:bg-riesgo-alto/10 transition-colors shrink-0"
      >
        <Trash2 size={18} aria-hidden="true" />
      </button>
    </div>
  )
}





