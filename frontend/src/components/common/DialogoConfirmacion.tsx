import { useEffect, useId, useRef } from 'react'

interface Props {
  abierto: boolean
  titulo: string
  mensaje: string
  textoConfirmar: string
  procesando?: boolean
  error?: string | null
  onConfirmar: () => void
  onCancelar: () => void
}

export default function DialogoConfirmacion({
  abierto,
  titulo,
  mensaje,
  textoConfirmar,
  procesando = false,
  error = null,
  onConfirmar,
  onCancelar,
}: Props) {
  const idTitulo = useId()
  const idMensaje = useId()
  const cancelarRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (abierto) cancelarRef.current?.focus()
  }, [abierto])

  if (!abierto) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onKeyDown={(e) => {
        if (e.key === 'Escape' && !procesando) onCancelar()
      }}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        aria-describedby={idMensaje}
        className="card w-full max-w-sm space-y-4"
      >
        <h2 id={idTitulo} className="text-lg font-semibold text-gray-900">
          {titulo}
        </h2>
        <p id={idMensaje} className="text-sm text-gray-600 leading-relaxed">
          {mensaje}
        </p>
        {error && (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <button
            ref={cancelarRef}
            type="button"
            onClick={onCancelar}
            disabled={procesando}
            className="btn-secondary text-sm"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={procesando}
            className="btn-primary text-sm"
          >
            {procesando ? 'Procesando...' : textoConfirmar}
          </button>
        </div>
      </div>
    </div>
  )
}
