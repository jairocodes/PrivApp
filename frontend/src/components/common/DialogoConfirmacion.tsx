import { Description, Dialog, DialogPanel, DialogTitle } from '@headlessui/react'

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

/** Confirmación de una acción irreversible. Headless UI mantiene el foco dentro
 *  del diálogo mientras está abierto y lo devuelve al cerrarse. */
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
  return (
    <Dialog
      open={abierto}
      role="alertdialog"
      // Escape o un clic fuera cancelan, salvo mientras la acción está en curso.
      onClose={() => {
        if (!procesando) onCancelar()
      }}
      className="relative z-50"
    >
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel className="card w-full max-w-sm space-y-4">
          <DialogTitle as="h2" className="text-lg font-bold text-texto">
            {titulo}
          </DialogTitle>
          <Description className="text-sm leading-relaxed text-texto-2">{mensaje}</Description>
          {error && (
            <p role="alert" className="text-sm text-riesgo-alto">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button type="button" autoFocus onClick={onCancelar} disabled={procesando} className="btn-secondary text-sm">
              Cancelar
            </button>
            <button type="button" onClick={onConfirmar} disabled={procesando} className="btn-primary text-sm">
              {procesando ? 'Procesando...' : textoConfirmar}
            </button>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  )
}
