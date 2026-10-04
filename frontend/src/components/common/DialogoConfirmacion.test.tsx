import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import DialogoConfirmacion from './DialogoConfirmacion'

function renderDialogo(props: Partial<Parameters<typeof DialogoConfirmacion>[0]> = {}) {
  const onConfirmar = vi.fn()
  const onCancelar = vi.fn()
  render(
    <DialogoConfirmacion
      abierto
      titulo="¿Eliminar?"
      mensaje="Esta acción no se puede deshacer."
      textoConfirmar="Eliminar"
      onConfirmar={onConfirmar}
      onCancelar={onCancelar}
      {...props}
    />,
  )
  return { onConfirmar, onCancelar }
}

describe('DialogoConfirmacion', () => {
  it('no se muestra cerrado', () => {
    renderDialogo({ abierto: false })
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })

  it('muestra título y mensaje, con el foco en Cancelar', () => {
    renderDialogo()
    const dialogo = screen.getByRole('alertdialog', { name: '¿Eliminar?' })
    expect(dialogo).toHaveAccessibleDescription('Esta acción no se puede deshacer.')
    expect(screen.getByRole('button', { name: 'Cancelar' })).toHaveFocus()
  })

  it('confirma o cancela', async () => {
    const { onConfirmar, onCancelar } = renderDialogo()

    await userEvent.click(screen.getByRole('button', { name: 'Eliminar' }))
    expect(onConfirmar).toHaveBeenCalledTimes(1)

    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(onCancelar).toHaveBeenCalledTimes(1)
  })

  it('Escape cancela', async () => {
    const { onCancelar } = renderDialogo()
    await userEvent.keyboard('{Escape}')
    expect(onCancelar).toHaveBeenCalled()
  })

  it('el foco no sale del diálogo al recorrerlo con Tab', async () => {
    renderDialogo()
    const cancelar = screen.getByRole('button', { name: 'Cancelar' })
    const eliminar = screen.getByRole('button', { name: 'Eliminar' })

    await userEvent.tab()
    expect(eliminar).toHaveFocus()
    await userEvent.tab()
    expect(cancelar).toHaveFocus()
  })

  it('mientras procesa, Escape no cierra el diálogo', async () => {
    const { onCancelar } = renderDialogo({ procesando: true })
    await userEvent.keyboard('{Escape}')
    expect(onCancelar).not.toHaveBeenCalled()
  })

  it('bloquea los botones mientras procesa y muestra errores', () => {
    renderDialogo({ procesando: true, error: 'Algo falló.' })
    expect(screen.getByRole('button', { name: 'Procesando...' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled()
    expect(screen.getByRole('alert')).toHaveTextContent('Algo falló.')
  })
})
