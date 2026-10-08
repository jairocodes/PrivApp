import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

interface Props {
  icono: LucideIcon
  mensaje: string
  /** Acción sugerida, por ejemplo un enlace para empezar. */
  accion?: ReactNode
}

/** Pantalla o lista sin contenido, con una salida clara. */
export default function EstadoVacio({ icono: Icono, mensaje, accion }: Props) {
  return (
    <div className="card flex flex-col items-center gap-3 py-12 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-marca-suave text-marca-texto">
        <Icono size={28} aria-hidden="true" />
      </span>
      <p className="text-sm text-texto-2">{mensaje}</p>
      {accion && <div className="mt-1">{accion}</div>}
    </div>
  )
}
