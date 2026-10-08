import EncabezadoPagina from '@/components/common/EncabezadoPagina'
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
      <a href={enlace.url} target="_blank" rel="noopener noreferrer" className="text-marca-texto hover:underline">
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
        {bloque.etiqueta && <strong className="font-semibold text-texto">{bloque.etiqueta} </strong>}
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
            {elemento.etiqueta && <strong className="font-semibold text-texto">{elemento.etiqueta} </strong>}
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
          <tr className="border-b border-borde">
            {bloque.encabezados.map((encabezado) => (
              <th key={encabezado} scope="col" className="py-2 pr-4 font-semibold text-texto">
                {encabezado}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bloque.filas.map(([dato, tiempo]) => (
            <tr key={dato} className="border-b border-borde align-top">
              <th scope="row" className="py-2 pr-4 font-normal text-texto">
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
    <main className="mx-auto max-w-3xl px-4 py-6 pb-16">
      <EncabezadoPagina titulo={TITULO_AVISO} subtitulo={`Última actualización: ${ULTIMA_ACTUALIZACION}`} />

      <nav aria-label="Contenido del aviso" className="card mb-5 p-5">
        <p className="mb-2 text-sm font-bold text-texto">En este aviso</p>
        <ol className="grid gap-1 text-sm sm:grid-cols-2">
          {SECCIONES_AVISO.map((seccion) => (
            <li key={seccion.id}>
              <a href={`#${seccion.id}`} className="inline-flex min-h-[36px] items-center text-marca-texto hover:underline">
                {seccion.titulo}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <article className="card space-y-8 text-base leading-relaxed text-texto-2 sm:p-8">
        <p>{INTRODUCCION}</p>
        {SECCIONES_AVISO.map((seccion) => (
          <section
            key={seccion.id}
            id={seccion.id}
            aria-labelledby={`titulo-${seccion.id}`}
            className="scroll-mt-24 space-y-3"
          >
            <h2 id={`titulo-${seccion.id}`} className="text-lg font-bold text-texto">
              {seccion.titulo}
            </h2>
            {seccion.bloques.map((bloque, i) => (
              <BloqueAviso key={i} bloque={bloque} />
            ))}
          </section>
        ))}
      </article>
    </main>
  )
}
