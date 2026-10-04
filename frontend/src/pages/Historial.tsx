import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FileSearch, Plus, Trash2 } from 'lucide-react'
import { analisisApi } from '@/api/analisis'
import Aviso from '@/components/common/Aviso'
import Cargando from '@/components/common/Cargando'
import DialogoConfirmacion from '@/components/common/DialogoConfirmacion'
import EncabezadoPagina from '@/components/common/EncabezadoPagina'
import EstadoVacio from '@/components/common/EstadoVacio'
import Paginacion from '@/components/common/Paginacion'
import IndicadorSemaforo from '@/components/analisis/IndicadorSemaforo'
import FormFiltrosHistorial from '@/components/historial/FormFiltrosHistorial'
import { useHistorial } from '@/hooks/useHistorial'
import type { AnalisisHistorialItem, FiltrosHistorial, NivelRiesgo } from '@/types/analisis'
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
      <main className="mx-auto max-w-2xl px-4 py-6 pb-16">
        <EncabezadoPagina titulo="Mis análisis" subtitulo="Tus análisis guardados. Solo tú los ves." />

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
            <div className="space-y-5">
              {agruparPorDia(items).map(({ dia, analisis }) => (
                <section key={dia} aria-label={dia} className="space-y-3">
                  <h2 className="px-1 text-sm font-bold text-texto-2">{dia}</h2>
                  {analisis.map((item) => (
                    <TarjetaHistorial
                      key={item.id_analisis}
                      item={item}
                      onEliminar={() => {
                        setErrorEliminar(null)
                        setPorEliminar(item)
                      }}
                    />
                  ))}
                </section>
              ))}
            </div>

            <Paginacion
              page={page}
              totalPaginas={totalPaginas}
              onCambiarPagina={cargar}
              disabled={isLoading}
            />

            <Link
              to="/analizar"
              className="mt-4 flex items-center gap-4 rounded-2xl border-2 border-dashed border-marca-borde p-4 text-marca-texto hover:bg-marca-suave/40"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-marca-suave">
                <Plus size={22} aria-hidden="true" />
              </span>
              <span>
                <span className="block font-bold">Analiza otra política</span>
                <span className="block text-sm text-texto-2">¿Usas otra app? Revisa qué hace con tus datos.</span>
              </span>
            </Link>
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

const COLOR_ANILLO: Record<NivelRiesgo, string> = {
  alto: '--riesgo-alto-solido',
  medio: '--riesgo-medio-solido',
  bajo: '--riesgo-bajo-solido',
}

function etiquetaDia(fecha: Date): string {
  const hoy = new Date()
  const ayer = new Date(hoy)
  ayer.setDate(hoy.getDate() - 1)
  if (fecha.toDateString() === hoy.toDateString()) return 'Hoy'
  if (fecha.toDateString() === ayer.toDateString()) return 'Ayer'
  return fecha.toLocaleDateString('es-GT', { day: 'numeric', month: 'long', year: 'numeric' })
}

/** Los análisis llegan del más reciente al más antiguo: se agrupan por día. */
function agruparPorDia(items: AnalisisHistorialItem[]) {
  const grupos: { dia: string; analisis: AnalisisHistorialItem[] }[] = []
  for (const item of items) {
    const dia = etiquetaDia(new Date(item.fecha))
    const ultimo = grupos[grupos.length - 1]
    if (ultimo?.dia === dia) ultimo.analisis.push(item)
    else grupos.push({ dia, analisis: [item] })
  }
  return grupos
}

function AnilloPuntuacion({ puntaje, nivel }: { puntaje: number; nivel: NivelRiesgo }) {
  const grados = Math.min(100, Math.max(0, puntaje)) * 3.6
  return (
    <span
      aria-hidden="true"
      className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full"
      style={{
        background: `conic-gradient(rgb(var(${COLOR_ANILLO[nivel]})) ${grados}deg, rgb(var(--superficie-2)) 0deg)`,
      }}
    >
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-superficie text-base font-extrabold text-texto">
        {puntaje}
      </span>
    </span>
  )
}

function TarjetaHistorial({ item, onEliminar }: { item: AnalisisHistorialItem; onEliminar: () => void }) {
  const fecha = new Date(item.fecha)
  const fechaFormateada = fecha.toLocaleString('es-GT', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
  const hora = fecha.toLocaleTimeString('es-GT', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="flex items-center gap-2 rounded-2xl border border-borde bg-superficie p-3 transition-colors hover:border-marca-borde sm:p-4">
      <Link to={`/resultados/${item.id_analisis}`} className="flex min-w-0 flex-1 items-center gap-3 sm:gap-4">
        <AnilloPuntuacion puntaje={item.puntaje} nivel={item.nivel_riesgo_global} />
        <span className="min-w-0 flex-1 space-y-1.5">
          <span className="block text-base leading-snug text-texto line-clamp-2">{item.comentario_breve}</span>
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <IndicadorSemaforo nivel={item.nivel_riesgo_global} size="sm" />
            <span className="text-sm text-texto-2">{hora}</span>
          </span>
        </span>
      </Link>
      <button
        type="button"
        onClick={onEliminar}
        aria-label={`Eliminar el análisis del ${fechaFormateada}`}
        className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-texto-3 transition-colors hover:bg-riesgo-alto/10 hover:text-riesgo-alto"
      >
        <Trash2 size={18} aria-hidden="true" />
      </button>
    </div>
  )
}
