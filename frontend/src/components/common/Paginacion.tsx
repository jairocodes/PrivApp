import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  page: number
  totalPaginas: number
  onCambiarPagina: (pagina: number) => void
  disabled?: boolean
}

const BOTON =
  'inline-flex min-h-[44px] items-center gap-1 rounded-xl px-3 text-sm font-semibold text-texto-2 ' +
  'hover:bg-superficie-2 hover:text-marca-texto disabled:cursor-not-allowed disabled:opacity-40'

export default function Paginacion({ page, totalPaginas, onCambiarPagina, disabled = false }: Props) {
  return (
    <nav aria-label="Paginación" className="mt-5 flex items-center justify-between">
      <button type="button" onClick={() => onCambiarPagina(page - 1)} disabled={disabled || page <= 1} className={BOTON}>
        <ChevronLeft size={18} aria-hidden="true" />
        Anterior
      </button>
      <span className="text-sm text-texto-2">
        Página {page} de {totalPaginas}
      </span>
      <button
        type="button"
        onClick={() => onCambiarPagina(page + 1)}
        disabled={disabled || page >= totalPaginas}
        className={BOTON}
      >
        Siguiente
        <ChevronRight size={18} aria-hidden="true" />
      </button>
    </nav>
  )
}
