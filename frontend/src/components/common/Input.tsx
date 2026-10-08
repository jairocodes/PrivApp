import type { InputHTMLAttributes, ReactNode } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  /** Indicación bajo el campo, asociada con aria-describedby. */
  ayuda?: ReactNode
}

export default function Input({ label, error, ayuda, id, ...props }: InputProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')
  const ayudaId = `${inputId}-ayuda`

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-semibold text-texto">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={ayuda ? ayudaId : undefined}
        className={`input-field ${error ? 'border-riesgo-alto' : ''}`}
        {...props}
      />
      {ayuda && (
        <p id={ayudaId} className="text-sm text-texto-2">
          {ayuda}
        </p>
      )}
      {error && <p className="text-sm text-riesgo-alto">{error}</p>}
    </div>
  )
}
