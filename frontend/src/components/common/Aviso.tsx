import type { ReactNode } from 'react'
import { CircleAlert, CircleCheck, Info } from 'lucide-react'

type TipoAviso = 'error' | 'exito' | 'info'

const ESTILOS: Record<TipoAviso, string> = {
  error: 'border-riesgo-alto/30 bg-riesgo-alto/10 text-riesgo-alto',
  exito: 'border-riesgo-bajo/30 bg-riesgo-bajo/10 text-riesgo-bajo',
  info: 'border-marca-borde bg-marca-suave text-marca-suave-texto',
}

const ICONOS = { error: CircleAlert, exito: CircleCheck, info: Info }

interface Props {
  tipo: TipoAviso
  children: ReactNode
  className?: string
}

/** Mensaje destacado. Los errores se anuncian de inmediato (role="alert");
 *  los demás, sin interrumpir (role="status"). */
export default function Aviso({ tipo, children, className = '' }: Props) {
  const Icono = ICONOS[tipo]
  return (
    <div
      role={tipo === 'error' ? 'alert' : 'status'}
      className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${ESTILOS[tipo]} ${className}`}
    >
      <Icono size={18} aria-hidden="true" className="mt-0.5 shrink-0" />
      <div className="min-w-0">{children}</div>
    </div>
  )
}
