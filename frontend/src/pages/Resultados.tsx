import { useEffect } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ArrowLeft, ShieldAlert, ShieldCheck } from 'lucide-react'
import Navbar from '@/components/common/Navbar'
import IndicadorSemaforo from '@/components/analisis/IndicadorSemaforo'
import TarjetaSeccion from '@/components/analisis/TarjetaSeccion'
import ListaRecomendaciones from '@/components/analisis/ListaRecomendaciones'
import { useAnalisis } from '@/hooks/useAnalisis'
import type { AnalisisResult } from '@/types/analisis'

export default function Resultados() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const { resultado, isLoading, error, obtener } = useAnalisis()

  const estadoInicial = (location.state as { resultado?: AnalisisResult } | null)?.resultado

  useEffect(() => {
    if (!estadoInicial && id) {
      obtener(id)
    }
  }, [id])

  const datos = estadoInicial ?? resultado

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

        {/* Estados de carga y error */}
        {isLoading && <EstadoCargando />}
        {error && !isLoading && <EstadoError mensaje={error} />}

        {/* Contenido principal */}
        {datos && !isLoading && <PanelResultados datos={datos} />}
      </main>
    </div>
  )
}

/* --------------------------------------------------------------------------
   Panel principal con todos los bloques
   -------------------------------------------------------------------------- */

function PanelResultados({ datos }: { datos: AnalisisResult }) {
  const { resumen_general, secciones_analizadas, recomendaciones, fecha } = datos
  const fechaFormateada = new Date(fecha).toLocaleString('es-GT', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

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

        <p className="text-sm text-gray-700 leading-relaxed">{resumen_general.comentario_breve}</p>

        {/* Estadísticas rápidas */}
        <div className="grid grid-cols-3 gap-3 pt-1">
          <Stat label="Secciones" valor={secciones_analizadas.length} />
          <Stat
            label="Hallazgos críticos"
            valor={totalHallazgosAltos}
            color={totalHallazgosAltos > 0 ? 'text-red-600' : 'text-green-600'}
          />
          <Stat label="Recomendaciones" valor={recomendaciones.length} />
        </div>
      </div>

      {/* ── Secciones analizadas ──────────────────────────────────────── */}
      <div>
        <h2 className="text-base font-semibold text-gray-700 mb-3 px-1">
          Secciones analizadas
        </h2>
        <div className="space-y-3">
          {secciones_analizadas.map((sec, i) => (
            <TarjetaSeccion
              key={i}
              seccion={sec}
              indice={i + 1}
              inicialmenteExpandida={i === 0}
            />
          ))}
        </div>
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

      {/* ── Acción final ──────────────────────────────────────────────── */}
      <div className="text-center pt-2">
        <Link
          to="/analizar"
          className="inline-flex items-center gap-2 btn-primary text-sm"
        >
          <ShieldCheck size={16} />
          Analizar otra política
        </Link>
      </div>

    </div>
  )
}

/* --------------------------------------------------------------------------
   Componentes auxiliares de UI
   -------------------------------------------------------------------------- */

function PuntajeCircular({ puntaje, nivel }: { puntaje: number; nivel: string }) {
  const colorArc: Record<string, string> = {
    bajo: 'text-green-500',
    medio: 'text-yellow-400',
    alto: 'text-red-500',
  }
  return (
    <div className="flex flex-col items-center justify-center w-16 h-16 rounded-full border-4
                    border-gray-100 bg-white shadow-sm shrink-0">
      <span className={`text-xl font-black leading-none ${colorArc[nivel] ?? 'text-gray-500'}`}>
        {puntaje}
      </span>
      <span className="text-xs text-gray-400 leading-none">/100</span>
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
