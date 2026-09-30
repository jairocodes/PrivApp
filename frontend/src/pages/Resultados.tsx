import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Download, ShieldAlert, ShieldCheck, Trash2 } from 'lucide-react'
import DialogoConfirmacion from '@/components/common/DialogoConfirmacion'
import Navbar from '@/components/common/Navbar'
import IndicadorSemaforo, { CONFIG as CONFIG_RIESGO } from '@/components/analisis/IndicadorSemaforo'
import TarjetaSeccion from '@/components/analisis/TarjetaSeccion'
import FiltroHallazgos from '@/components/analisis/FiltroHallazgos'
import ListaRecomendaciones from '@/components/analisis/ListaRecomendaciones'
import AyudaGlosario from '@/components/glosario/AyudaGlosario'
import VistaProgreso from '@/components/analisis/VistaProgreso'
import { useAnalisis } from '@/hooks/useAnalisis'
import { useProgresoAnalisis } from '@/hooks/useProgresoAnalisis'
import { analisisApi } from '@/api/analisis'
import type { AnalisisResult, NivelRiesgo } from '@/types/analisis'
import {
  SIN_FILTRO,
  contarHallazgos,
  filtrarSecciones,
  hayFiltroActivo,
  type FiltroHallazgos as Filtro,
} from '@/utils/filtrosHallazgos'
import {
  MENSAJE_ELIMINAR_ANALISIS,
  MENSAJE_LIMITE_SOLICITUDES,
  detalleDeError,
  esLimiteDeSolicitudes,
} from '@/utils/errores'

export default function Resultados() {
  const { id } = useParams<{ id: string }>()
  const { resultado, isLoading, error, obtener } = useAnalisis()
  const { estado, seccionActual, seccionesTotal } = useProgresoAnalisis(id)

  // El análisis (nuevo o ya completado, ej. desde el historial) siempre pasa
  // primero por /estado: si ya está "completado" ese primer sondeo responde
  // de inmediato y este efecto trae el resultado sin espera perceptible.
  useEffect(() => {
    if (id && estado === 'completado') {
      obtener(id)
    }
  }, [id, estado])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        {/* Encabezado */}
        <div className="flex items-center gap-3 mb-6">
          <Link
            to="/analizar"
            className="p-2 rounded-lg hover:bg-gray-200 text-gray-500 transition-colors"
            aria-label="Volver a analizar"
          >
            <ArrowLeft size={20} />
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Resultados del análisis</h1>
        </div>

        {/* Vista de progreso mientras el análisis está en curso (HU-13) */}
        {estado === 'procesando' && (
          <VistaProgreso seccionActual={seccionActual} seccionesTotal={seccionesTotal} />
        )}
        {estado === 'error' && (
          <EstadoError mensaje="Ocurrió un error durante el análisis. Intenta nuevamente." />
        )}

        {/* Resultado ya completado */}
        {estado === 'completado' && isLoading && <EstadoCargando />}
        {estado === 'completado' && error && !isLoading && <EstadoError mensaje={error} />}
        {estado === 'completado' && resultado && !isLoading && (
          <PanelResultados datos={resultado} />
        )}
      </main>
    </div>
  )
}

/* --------------------------------------------------------------------------
   Panel principal con todos los bloques
   -------------------------------------------------------------------------- */

function PanelResultados({ datos }: { datos: AnalisisResult }) {
  const { resumen_general, secciones_analizadas, recomendaciones, fecha, id_analisis } = datos
  const fechaFormateada = new Date(fecha).toLocaleString('es-GT', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

  const [descargando, setDescargando] = useState(false)
  const [filtro, setFiltro] = useState<Filtro>(SIN_FILTRO)
  const seccionesVisibles = filtrarSecciones(secciones_analizadas, filtro)
  const filtroActivo = hayFiltroActivo(filtro)
  const [errorDescarga, setErrorDescarga] = useState<string | null>(null)
  const navigate = useNavigate()
  const [confirmandoEliminar, setConfirmandoEliminar] = useState(false)
  const [eliminando, setEliminando] = useState(false)
  const [errorEliminar, setErrorEliminar] = useState<string | null>(null)

  const eliminar = async () => {
    setEliminando(true)
    setErrorEliminar(null)
    try {
      await analisisApi.eliminar(id_analisis)
      navigate('/historial', { replace: true, state: { mensaje: 'El análisis se eliminó.' } })
    } catch (err: unknown) {
      setErrorEliminar(detalleDeError(err, 'No fue posible eliminar el análisis. Intenta nuevamente.'))
      setEliminando(false)
    }
  }

  const descargarPDF = async () => {
    setDescargando(true)
    setErrorDescarga(null)
    try {
      const res = await analisisApi.descargarPDF(id_analisis)
      const url = window.URL.createObjectURL(res.data)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = `privapp-analisis-${id_analisis}.pdf`
      document.body.appendChild(enlace)
      enlace.click()
      enlace.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: unknown) {
      setErrorDescarga(
        esLimiteDeSolicitudes(err)
          ? MENSAJE_LIMITE_SOLICITUDES
          : 'No fue posible descargar el PDF. Intenta nuevamente.',
      )
    } finally {
      setDescargando(false)
    }
  }

  const totalHallazgosAltos = secciones_analizadas
    .flatMap((s) => s.hallazgos)
    .filter((h) => h.nivel === 'alto').length

  return (
    <div className="space-y-5">

      {/* ── Resumen ejecutivo ─────────────────────────────────────────── */}
      <div className="card space-y-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Resumen ejecutivo</h2>
            <p className="text-xs text-gray-400 mt-0.5">{fechaFormateada}</p>
          </div>
          {/* Puntaje visual */}
          <PuntajeCircular puntaje={resumen_general.puntaje} nivel={resumen_general.nivel_riesgo_global} />
        </div>

        <IndicadorSemaforo nivel={resumen_general.nivel_riesgo_global} size="lg" mostrarTexto />

        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
          <span className="inline-flex items-center gap-1">
            Nivel de riesgo <AyudaGlosario termino="Nivel de riesgo" />
          </span>
          <span className="inline-flex items-center gap-1">
            Puntaje de riesgo <AyudaGlosario termino="Puntaje de riesgo" />
          </span>
        </p>

        <p className="text-sm text-gray-700 leading-relaxed">{resumen_general.comentario_breve}</p>

        {/* Estadísticas rápidas */}
        <div className="grid grid-cols-3 gap-3 pt-1">
          <Stat label="Secciones" valor={secciones_analizadas.length} />
          <Stat
            label="Hallazgos críticos"
            valor={totalHallazgosAltos}
            color={totalHallazgosAltos > 0 ? 'text-riesgo-alto' : 'text-riesgo-bajo'}
          />
          <Stat label="Recomendaciones" valor={recomendaciones.length} />
        </div>
      </div>

      {/* ── Secciones analizadas ──────────────────────────────────────── */}
      <div>
        <h2 className="text-base font-semibold text-gray-700 mb-3 px-1">
          Secciones analizadas
        </h2>
        <div className="mb-3">
          <FiltroHallazgos
            filtro={filtro}
            onCambiar={setFiltro}
            visibles={contarHallazgos(seccionesVisibles.map((s) => s.seccion))}
            total={contarHallazgos(secciones_analizadas)}
          />
        </div>
        {seccionesVisibles.length === 0 ? (
          <div className="card text-center py-8 space-y-2">
            <p className="text-sm text-gray-500">Ningún hallazgo coincide con los filtros.</p>
            <button
              type="button"
              onClick={() => setFiltro(SIN_FILTRO)}
              className="text-sm font-medium text-blue-600 hover:underline"
            >
              Mostrar todos los hallazgos
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {seccionesVisibles.map(({ seccion, indice }, posicion) => (
              <TarjetaSeccion
                // La clave cambia con el filtro para que las secciones se abran al filtrar.
                key={`${indice}-${filtro.nivel}-${filtro.jurisdiccion}`}
                seccion={seccion}
                indice={indice}
                inicialmenteExpandida={filtroActivo || posicion === 0}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Recomendaciones ───────────────────────────────────────────── */}
      <ListaRecomendaciones recomendaciones={recomendaciones} />

      {/* ── Aviso académico ───────────────────────────────────────────── */}
      <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
        <div className="flex items-start gap-2">
          <ShieldAlert size={16} className="text-blue-500 shrink-0 mt-0.5" />
          <p className="text-xs text-blue-700 leading-relaxed">
            Este análisis es orientativo y no constituye asesoría legal. Las referencias
            internacionales (RGPD, Principios OEA, etc.) son buenas prácticas, no normativa
            vigente en Guatemala. Para dudas legales, consulta a un profesional.
          </p>
        </div>
      </div>

      {/* ── Acciones finales ──────────────────────────────────────────── */}
      <div className="text-center pt-2 space-y-3">
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <button
            onClick={descargarPDF}
            disabled={descargando}
            className="inline-flex items-center gap-2 btn-primary text-sm disabled:opacity-60"
          >
            <Download size={16} />
            {descargando ? 'Generando PDF...' : 'Descargar PDF'}
          </button>
          <Link
            to="/analizar"
            className="inline-flex items-center gap-2 btn-primary text-sm"
          >
            <ShieldCheck size={16} />
            Analizar otra política
          </Link>
          <button
            type="button"
            onClick={() => {
              setErrorEliminar(null)
              setConfirmandoEliminar(true)
            }}
            className="inline-flex items-center gap-2 btn-secondary text-sm text-red-700"
          >
            <Trash2 size={16} aria-hidden="true" />
            Eliminar análisis
          </button>
        </div>
        {errorDescarga && <p className="text-xs text-red-600">{errorDescarga}</p>}
      </div>

      <DialogoConfirmacion
        abierto={confirmandoEliminar}
        titulo="¿Eliminar este análisis?"
        mensaje={MENSAJE_ELIMINAR_ANALISIS}
        textoConfirmar="Eliminar"
        procesando={eliminando}
        error={errorEliminar}
        onConfirmar={eliminar}
        onCancelar={() => setConfirmandoEliminar(false)}
      />

    </div>
  )
}

/* --------------------------------------------------------------------------
   Componentes auxiliares de UI
   -------------------------------------------------------------------------- */

function PuntajeCircular({ puntaje, nivel }: { puntaje: number; nivel: NivelRiesgo }) {
  const colorArc: Record<NivelRiesgo, string> = {
    bajo: 'text-riesgo-bajo',
    medio: 'text-riesgo-medio',
    alto: 'text-riesgo-alto',
  }
  return (
    <div
      role="img"
      aria-label={`Puntaje de riesgo: ${puntaje} de 100, ${CONFIG_RIESGO[nivel].label}`}
      className="flex flex-col items-center justify-center w-16 h-16 rounded-full border-4
                    border-gray-100 bg-white shadow-sm shrink-0"
    >
      <span className={`text-xl font-black leading-none ${colorArc[nivel] ?? 'text-gray-500'}`} aria-hidden="true">
        {puntaje}
      </span>
      <span className="text-xs text-gray-400 leading-none" aria-hidden="true">/100</span>
    </div>
  )
}

function Stat({ label, valor, color = 'text-gray-900' }: { label: string; valor: number; color?: string }) {
  return (
    <div className="rounded-lg bg-gray-50 px-3 py-2 text-center">
      <p className={`text-xl font-bold ${color}`}>{valor}</p>
      <p className="text-xs text-gray-500 leading-tight mt-0.5">{label}</p>
    </div>
  )
}

function EstadoCargando() {
  return (
    <div className="card text-center py-16 space-y-3">
      <div className="inline-flex w-12 h-12 rounded-full border-4 border-blue-200 border-t-blue-600
                      animate-spin mx-auto" />
      <p className="text-gray-500 text-sm">Cargando análisis...</p>
    </div>
  )
}

function EstadoError({ mensaje }: { mensaje: string }) {
  return (
    <div className="card bg-red-50 border-red-200 text-center py-10 space-y-3">
      <ShieldAlert size={32} className="text-red-400 mx-auto" />
      <p className="text-red-700 text-sm">{mensaje}</p>
      <Link to="/analizar" className="inline-block btn-primary text-sm mt-2">
        Intentar de nuevo
      </Link>
    </div>
  )
}
