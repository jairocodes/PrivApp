interface SpinnerProps {
  /** Nombre accesible; sin él, el spinner es decorativo. */
  etiqueta?: string
  className?: string
}

export function Spinner({ etiqueta, className = 'h-12 w-12' }: SpinnerProps) {
  return (
    <div
      role={etiqueta ? 'status' : undefined}
      aria-label={etiqueta}
      aria-hidden={etiqueta ? undefined : true}
      className={`inline-flex rounded-full border-4 border-marca-suave border-t-marca animate-spin motion-reduce:animate-none ${className}`}
    />
  )
}

/** Tarjeta de carga de una pantalla o sección, con su mensaje. */
export default function Cargando({ mensaje }: { mensaje: string }) {
  return (
    <div role="status" className="card flex flex-col items-center gap-3 py-16 text-center">
      <Spinner />
      <p className="text-sm text-texto-2">{mensaje}</p>
    </div>
  )
}
