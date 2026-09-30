import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { crearAuthValue, usuarioComun } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import FormCambioPassword from './FormCambioPassword'

function renderForm(auth: AuthContextValue) {
  render(
    <AuthContext.Provider value={auth}>
      <FormCambioPassword />
    </AuthContext.Provider>,
  )
}

async function completar(actual: string, nueva: string, confirmacion = nueva) {
  if (actual) await userEvent.type(screen.getByLabelText('Contraseña actual'), actual)
  if (nueva) await userEvent.type(screen.getByLabelText('Nueva contraseña'), nueva)
  if (confirmacion) await userEvent.type(screen.getByLabelText('Confirmar nueva contraseña'), confirmacion)
  await userEvent.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))
}

describe('FormCambioPassword', () => {
  it('cambia la contraseña, limpia el formulario y avisa del cierre de otras sesiones', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await completar('Actual123', 'Nueva4567')

    expect(auth.cambiarPassword).toHaveBeenCalledWith({
      password_actual: 'Actual123',
      password_nueva: 'Nueva4567',
      confirmar_password: 'Nueva4567',
    })
    expect(await screen.findByRole('status')).toHaveTextContent('Se cerraron las sesiones abiertas')
    expect(screen.getByLabelText('Contraseña actual')).toHaveValue('')
    expect(screen.getByLabelText('Nueva contraseña')).toHaveValue('')
  })

  it('exige la contraseña actual', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await completar('', 'Nueva4567')

    expect(screen.getByText('Ingresa tu contraseña actual.')).toBeInTheDocument()
    expect(auth.cambiarPassword).not.toHaveBeenCalled()
  })

  it('aplica las reglas de fortaleza a la nueva contraseña', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await completar('Actual123', 'debil')

    expect(screen.getByText('La contraseña debe tener al menos 8 caracteres.')).toBeInTheDocument()
    expect(auth.cambiarPassword).not.toHaveBeenCalled()
  })

  it('exige que la nueva sea distinta de la actual', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await completar('Actual123', 'Actual123')

    expect(screen.getByText('La nueva contraseña debe ser distinta de la actual.')).toBeInTheDocument()
    expect(auth.cambiarPassword).not.toHaveBeenCalled()
  })

  it('exige que la confirmación coincida', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await completar('Actual123', 'Nueva4567', 'Distinta890')

    expect(screen.getByText('La confirmación no coincide con la nueva contraseña.')).toBeInTheDocument()
    expect(auth.cambiarPassword).not.toHaveBeenCalled()
  })

  it('muestra junto al campo que la contraseña actual es incorrecta', async () => {
    const auth = crearAuthValue({
      user: usuarioComun,
      token: 't',
      cambiarPassword: vi.fn().mockRejectedValue({
        response: { status: 400, data: { detail: 'La contraseña actual es incorrecta.' } },
      }),
    })
    renderForm(auth)

    await completar('Incorrecta1', 'Nueva4567')

    expect(await screen.findByText('La contraseña actual es incorrecta.')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('muestra un error genérico ante otros fallos', async () => {
    const auth = crearAuthValue({
      user: usuarioComun,
      token: 't',
      cambiarPassword: vi.fn().mockRejectedValue({ response: { status: 500 } }),
    })
    renderForm(auth)

    await completar('Actual123', 'Nueva4567')

    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cambiar tu contraseña.')
  })
})
