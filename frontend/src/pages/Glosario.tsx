import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import Navbar from '@/components/common/Navbar'
import { buscarEnGlosario } from '@/data/glosario'

export default function Glosario() {
  const [consulta, setConsulta] = useState('')
  const entradas = buscarEnGlosario(consulta)
  const { hash } = useLocation()

  // Al llegar desde la ayuda de los resultados (/glosario#termino), baja hasta ese término.
  useEffect(() => {
    if (hash) document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView()
  }, [hash])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16 space-y-5">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Glosario</h1>
          <p className="text-sm text-gray-500 mt-1">
            Términos que aparecen en los resultados del análisis, explicados en lenguaje sencillo.
          </p>
        </div>

        <div role="search">
          <label htmlFor="busqueda-glosario" className="sr-only">
            Buscar un término
          </label>
          <input
            id="busqueda-glosario"
            type="search"
            value={consulta}
            onChange={(e) => setConsulta(e.target.value)}
            placeholder="Buscar un término"
            className="input-field w-full"
          />
          <p className="text-xs text-gray-400 mt-1" aria-live="polite">
            {entradas.length === 1 ? '1 término' : `${entradas.length} términos`}
          </p>
        </div>

        {entradas.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-10">
            No se encontraron términos para «{consulta.trim()}».
          </p>
        ) : (
          <dl className="space-y-3">
            {entradas.map((entrada) => (
              <div key={entrada.id} id={entrada.id} className="card scroll-mt-4">
                <dt className="font-semibold text-gray-900">{entrada.termino}</dt>
                <dd className="text-sm text-gray-700 mt-1 leading-relaxed">{entrada.definicion}</dd>
              </div>
            ))}
          </dl>
        )}
      </main>
    </div>
  )
}
