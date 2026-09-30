import { Suspense, lazy, useEffect, useState } from 'react'
import { analisisApi } from '@/api/analisis'
import type { EstadisticasPersonales } from '@/types/analisis'

// recharts se descarga aparte y solo cuando hay datos que graficar, para no
// cargarlo en el resto de las pantallas (se usa desde teléfonos).
const GraficoDistribucion = lazy(() => import('@/components/dashboard/GraficoDistribucion'))

export default function PanelEstadistico() {
  const [datos, setDatos] = useState<EstadisticasPersonales | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    analisisApi
      .estadisticas()
      .then(({ data }) => setDatos(data))
      .catch(() => setError('No fue posible cargar tus estadísticas.'))
  }, [])

  return (
    <section aria-labelledby="titulo-estadisticas" className="card space-y-4">
      <h2 id="titulo-estadisticas" className="font-semibold text-gray-900">
        Mis estadísticas
      </h2>

      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      {!error && !datos && <p className="text-sm text-gray-500">Cargando estadísticas...</p>}

      {datos && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Indicador etiqueta="Análisis realizados" valor={datos.total.toLocaleString('es-GT')} />
            <Indicador
              etiqueta="Puntaje promedio"
              valor={`${datos.puntaje_promedio.toLocaleString('es-GT', { maximumFractionDigits: 1 })}/100`}
            />
          </div>

          {datos.total === 0 ? (
            <p className="text-sm text-gray-500">
              Aún no tienes análisis. Cuando analices una política, aquí verás cuántas son de riesgo bajo, medio o alto.
            </p>
          ) : (
            <Suspense fallback={<div className="h-44" aria-hidden="true" />}>
              <GraficoDistribucion distribucion={datos.por_nivel} />
            </Suspense>
          )}

          <ul aria-label="Análisis por nivel de riesgo" className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
            <li>
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-riesgo-bajo mr-1.5" aria-hidden="true" />
              Bajo: {datos.por_nivel.bajo}
            </li>
            <li>
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-riesgo-medio mr-1.5" aria-hidden="true" />
              Medio: {datos.por_nivel.medio}
            </li>
            <li>
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-riesgo-alto mr-1.5" aria-hidden="true" />
              Alto: {datos.por_nivel.alto}
            </li>
          </ul>
        </>
      )}
    </section>
  )
}

function Indicador({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="rounded-lg bg-gray-50 px-3 py-2 text-center">
      <p className="text-xl font-bold text-gray-900">{valor}</p>
      <p className="text-xs text-gray-500 leading-tight mt-0.5">{etiqueta}</p>
    </div>
  )
}
