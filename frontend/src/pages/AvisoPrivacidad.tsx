import Navbar from '@/components/common/Navbar'
import {
  INTRODUCCION,
  SECCIONES_AVISO,
  TITULO_AVISO,
  ULTIMA_ACTUALIZACION,
  type Bloque,
  type Enlace,
} from '@/data/avisoPrivacidad'

function EnlaceExterno({ enlace }: { enlace: Enlace }) {
  return (
    <>
      {' '}
      <a href={enlace.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
        {enlace.texto}
      </a>
      .
    </>
  )
}

function BloqueAviso({ bloque }: { bloque: Bloque }) {
  if (bloque.tipo === 'parrafo') {
    return (
      <p>
        {bloque.etiqueta && <strong className="font-semibold text-gray-900">{bloque.etiqueta} </strong>}
        {bloque.texto}
        {bloque.enlace && <EnlaceExterno enlace={bloque.enlace} />}
      </p>
    )
  }

  if (bloque.tipo === 'lista') {
    return (
      <ul className="list-disc pl-5 space-y-2">
        {bloque.elementos.map((elemento, i) => (
          <li key={i}>
            {elemento.etiqueta && <strong className="font-semibold text-gray-900">{elemento.etiqueta} </strong>}
            {elemento.texto}
            {elemento.enlace && <EnlaceExterno enlace={elemento.enlace} />}
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-gray-200">
            {bloque.encabezados.map((encabezado) => (
              <th key={encabezado} scope="col" className="py-2 pr-4 font-semibold text-gray-900">
                {encabezado}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bloque.filas.map(([dato, tiempo]) => (
            <tr key={dato} className="border-b border-gray-100 align-top">
              <th scope="row" className="py-2 pr-4 font-normal text-gray-800">
                {dato}
              </th>
              <td className="py-2">{tiempo}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function AvisoPrivacidad() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        <h1 className="text-xl font-bold text-gray-900">{TITULO_AVISO}</h1>
        <p className="text-xs text-gray-500 mt-1 mb-4">Última actualización: {ULTIMA_ACTUALIZACION}</p>

        <article className="card text-sm text-gray-700 leading-relaxed space-y-6">
          <p>{INTRODUCCION}</p>
          {SECCIONES_AVISO.map((seccion) => (
            <section key={seccion.id} id={seccion.id} aria-labelledby={`titulo-${seccion.id}`} className="space-y-3">
              <h2 id={`titulo-${seccion.id}`} className="text-base font-semibold text-gray-900">
                {seccion.titulo}
              </h2>
              {seccion.bloques.map((bloque, i) => (
                <BloqueAviso key={i} bloque={bloque} />
              ))}
            </section>
          ))}
        </article>
      </main>
    </div>
  )
}
