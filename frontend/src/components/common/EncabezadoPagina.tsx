import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'

interface Props {
  titulo: string
  subtitulo?: ReactNode
  /** Ruta del botón de volver; sin ella no se muestra. */
  volverA?: string
  etiquetaVolver?: string
  /** Acciones a la derecha del título. */
  acciones?: ReactNode
}

export default function EncabezadoPagina({ titulo, subtitulo, volverA, etiquetaVolver = 'Volver', acciones }: Props) {
  return (
    <div className="mb-6 flex items-center gap-2">
      {volverA && (
        <Link
          to={volverA}
          aria-label={etiquetaVolver}
          className="-ml-2 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-texto hover:bg-superficie-2"
        >
          <ChevronLeft size={24} aria-hidden="true" />
        </Link>
      )}
      <div className="min-w-0 flex-1">
        <h1 className="text-2xl font-extrabold tracking-tight text-texto">{titulo}</h1>
        {subtitulo && <p className="mt-1 text-sm text-texto-2">{subtitulo}</p>}
      </div>
      {acciones && <div className="flex shrink-0 items-center gap-2">{acciones}</div>}
    </div>
  )
}
