import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variante = 'primary' | 'secondary' | 'ghost' | 'danger'

const CLASES: Record<Variante, string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  ghost:
    'inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl px-4 py-2.5 font-semibold text-texto-2 ' +
    'hover:bg-superficie-2 hover:text-texto disabled:cursor-not-allowed disabled:opacity-50 transition-colors',
  danger:
    'inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl px-4 py-2.5 font-semibold ' +
    'border border-riesgo-alto/30 bg-superficie text-riesgo-alto hover:bg-riesgo-alto/10 ' +
    'disabled:cursor-not-allowed disabled:opacity-50 transition-colors',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variante
  isLoading?: boolean
  children: ReactNode
}

export default function Button({
  variant = 'primary',
  isLoading = false,
  children,
  disabled,
  className = '',
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button type={type} disabled={disabled || isLoading} className={`${CLASES[variant]} ${className}`} {...props}>
      {isLoading ? 'Cargando...' : children}
    </button>
  )
}
