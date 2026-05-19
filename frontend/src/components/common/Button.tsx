import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  isLoading?: boolean
  children: ReactNode
}

export default function Button({
  variant = 'primary',
  isLoading = false,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className={`${variant === 'primary' ? 'btn-primary' : 'btn-secondary'} ${className}`}
      {...props}
    >
      {isLoading ? 'Cargando...' : children}
    </button>
  )
}
