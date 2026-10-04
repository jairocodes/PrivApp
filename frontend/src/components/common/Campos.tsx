import { useId } from 'react'
import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'

const ETIQUETA = 'text-sm font-semibold text-texto'
const ERROR = 'text-sm text-riesgo-alto'
const CON_ERROR = 'border-riesgo-alto'

function Ayuda({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p id={id} className="text-sm text-texto-2">
      {children}
    </p>
  )
}

interface CampoSeleccionProps extends SelectHTMLAttributes<HTMLSelectElement> {
  etiqueta: string
  ayuda?: ReactNode
  error?: string
  children: ReactNode
}

export function CampoSeleccion({ etiqueta, ayuda, error, id, className = '', children, ...props }: CampoSeleccionProps) {
  const autoId = useId()
  const campoId = id ?? autoId
  const ayudaId = `${campoId}-ayuda`
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={campoId} className={ETIQUETA}>
        {etiqueta}
      </label>
      <select
        id={campoId}
        aria-invalid={error ? true : undefined}
        aria-describedby={ayuda ? ayudaId : undefined}
        className={`input-field ${error ? CON_ERROR : ''} ${className}`}
        {...props}
      >
        {children}
      </select>
      {ayuda && <Ayuda id={ayudaId}>{ayuda}</Ayuda>}
      {error && <p className={ERROR}>{error}</p>}
    </div>
  )
}

interface AreaTextoProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  etiqueta: string
  ayuda?: ReactNode
  error?: string
}

export function AreaTexto({ etiqueta, ayuda, error, id, className = '', ...props }: AreaTextoProps) {
  const autoId = useId()
  const campoId = id ?? autoId
  const ayudaId = `${campoId}-ayuda`
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={campoId} className={ETIQUETA}>
        {etiqueta}
      </label>
      <textarea
        id={campoId}
        aria-invalid={error ? true : undefined}
        aria-describedby={ayuda ? ayudaId : undefined}
        className={`input-field resize-y ${error ? CON_ERROR : ''} ${className}`}
        {...props}
      />
      {ayuda && <Ayuda id={ayudaId}>{ayuda}</Ayuda>}
      {error && <p className={ERROR}>{error}</p>}
    </div>
  )
}

interface CasillaProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  /** Texto de la casilla; puede incluir enlaces. */
  children: ReactNode
  error?: string
}

export function Casilla({ children, error, id, className = '', ...props }: CasillaProps) {
  const autoId = useId()
  const campoId = id ?? autoId
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-start gap-3">
        <input
          id={campoId}
          type="checkbox"
          aria-invalid={error ? true : undefined}
          className={`mt-0.5 h-5 w-5 shrink-0 rounded border-borde-fuerte accent-marca ${className}`}
          {...props}
        />
        <label htmlFor={campoId} className="text-sm leading-relaxed text-texto">
          {children}
        </label>
      </div>
      {error && <p className={`${ERROR} pl-8`}>{error}</p>}
    </div>
  )
}
