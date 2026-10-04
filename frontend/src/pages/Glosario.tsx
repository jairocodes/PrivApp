import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { BookOpen, Search } from 'lucide-react'
import EncabezadoPagina from '@/components/common/EncabezadoPagina'
import EstadoVacio from '@/components/common/EstadoVacio'
import { buscarEnGlosario } from '@/data/glosario'

export default function Glosario() {
  const [consulta, setConsulta] = useState('')
  const entradas = buscarEnGlosario(consulta)
  const { hash } = useLocation()

  // Al llegar desde la ayuda de los resultados (/glosario#termino), baja hasta ese término.
  useEffect(() => {
    if (hash) document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView?.()
  }, [hash])

  return (
    <main className="mx-auto max-w-5xl px-4 py-6 pb-16">
      <EncabezadoPagina
        titulo="Glosario"
        subtitulo="Términos que aparecen en los resultados del análisis, explicados en lenguaje sencillo."
      />

      <div role="search" className="mb-5 max-w-xl">
        <label htmlFor="busqueda-glosario" className="sr-only">
          Buscar un término
        </label>
        <div className="relative">
          <Search
            size={20}
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-texto-2"
          />
          <input
            id="busqueda-glosario"
            type="search"
            value={consulta}
            onChange={(e) => setConsulta(e.target.value)}
            placeholder="Buscar un término"
            className="input-field pl-10"
          />
        </div>
        <p className="mt-1.5 text-sm text-texto-2" aria-live="polite">
          {entradas.length === 1 ? '1 término' : `${entradas.length} términos`}
        </p>
      </div>

      {entradas.length === 0 ? (
        <EstadoVacio icono={BookOpen} mensaje={`No se encontraron términos para «${consulta.trim()}».`} />
      ) : (
        // Columnas que se rellenan de arriba abajo (como un tablero de tarjetas).
        <dl className="gap-4 sm:columns-2 lg:columns-3">
          {entradas.map((entrada) => (
            <div
              key={entrada.id}
              id={entrada.id}
              className="mb-4 scroll-mt-24 break-inside-avoid rounded-2xl border border-borde bg-superficie p-5 target:border-marca target:ring-2 target:ring-marca"
            >
              <dt className="text-base font-bold text-texto">{entrada.termino}</dt>
              <dd className="mt-1.5 text-sm leading-relaxed text-texto-2">{entrada.definicion}</dd>
            </div>
          ))}
        </dl>
      )}
    </main>
  )
}
