import { useEffect } from 'react'
import { useLocation, useParams, Link } from 'react-router-dom'
import Navbar from '@/components/common/Navbar'
import IndicadorSemaforo from '@/components/analisis/IndicadorSemaforo'
import { useAnalisis } from '@/hooks/useAnalisis'
import type { AnalisisResult } from '@/types/analisis'

export default function Resultados() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const { resultado, isLoading, error, obtener } = useAnalisis()

  // Si venimos de IngestaForm con el resultado en el state, lo usamos directamente
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
      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Resultados del análisis</h1>
          <Link to="/analizar" className="text-sm text-blue-600 hover:underline">
            Nuevo análisis
          </Link>
        </div>

        {isLoading && (
          <div className="card text-center py-12">
            <p className="text-gray-500">Cargando análisis...</p>
          </div>
        )}

        {error && (
          <div className="card bg-red-50 border-red-200">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {datos && <VistaResultados datos={datos} />}
      </main>
    </div>
  )
}

function VistaResultados({ datos }: { datos: AnalisisResult }) {
  const { resumen_general, secciones_analizadas, recomendaciones } = datos

  return (
    <div className="space-y-6">
      {/* Resumen general */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Resumen general</h2>
        <div className="flex items-center gap-4 mb-3">
          <IndicadorSemaforo nivel={resumen_general.nivel_riesgo_global} />
          <span className="text-2xl font-bold text-gray-800">
            {resumen_general.puntaje}/100
          </span>
        </div>
        <p className="text-gray-700 text-sm">{resumen_general.comentario_breve}</p>
      </div>

      {/* Secciones analizadas */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Secciones analizadas ({secciones_analizadas.length})
        </h2>
        <div className="space-y-4">
          {secciones_analizadas.map((sec, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-medium text-gray-900">{sec.titulo}</h3>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded shrink-0">
                  {sec.categoria_opp115}
                </span>
              </div>

              {sec.hallazgos.length > 0 ? (
                <ul className="space-y-2 mt-3">
                  {sec.hallazgos.map((h, j) => (
                    <li key={j} className="text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <NivelBadge nivel={h.nivel} />
                        <span className="text-gray-700">{h.descripcion}</span>
                      </div>
                      {h.fuentes_normativas.length > 0 && (
                        <ul className="ml-4 mt-1 space-y-0.5">
                          {h.fuentes_normativas.map((fn, k) => (
                            <li key={k} className="text-xs text-gray-500">
                              <span className="font-medium">{fn.documento}</span>
                              {fn.referencia && ` — ${fn.referencia}`}
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500 mt-2">Sin hallazgos en esta sección.</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recomendaciones */}
      {recomendaciones.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Recomendaciones</h2>
          <ul className="space-y-2">
            {recomendaciones.map((rec, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-700">
                <span className="text-blue-500 shrink-0">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-gray-400 text-center pb-4">
        Este análisis es orientativo y no constituye asesoría legal. Las referencias
        internacionales son buenas prácticas, no normativa vigente en Guatemala.
      </p>
    </div>
  )
}

function NivelBadge({ nivel }: { nivel: string }) {
  const config: Record<string, string> = {
    alto: 'bg-red-100 text-red-700',
    medio: 'bg-yellow-100 text-yellow-700',
    bajo: 'bg-green-100 text-green-700',
    neutral: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium shrink-0 ${config[nivel] ?? config.neutral}`}>
      {nivel}
    </span>
  )
}
