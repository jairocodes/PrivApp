import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import Login from '@/pages/Login'
import { crearAuthValue, usuarioComun } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import FormEliminarCuenta, { MENSAJE_CUENTA_ELIMINADA } from './FormEliminarCuenta'

function renderForm(auth: AuthContextValue) {
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={['/perfil']}>
        <Routes>
          <Route path="/perfil" element={<FormEliminarCuenta />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

const errorHttp = (status: number, detail?: string) => ({ response: { status, data: { detail } } })

async function solicitarEliminacion(password = 'MiClave123') {
  if (password) await userEvent.type(screen.getByLabelText('Contraseña'), password)
  await userEvent.click(screen.getByRole('button', { name: 'Eliminar mi cuenta' }))
}

describe('FormEliminarCuenta', () => {
  it('pide la contraseña antes de abrir la confirmación', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await solicitarEliminacion('')

    expect(screen.getByText('Ingresa tu contraseña para confirmar.')).toBeInTheDocument()
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(auth.eliminarCuenta).not.toHaveBeenCalled()
  })

  it('cancelar la confirmación no elimina nada', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await solicitarEliminacion()
    expect(screen.getByRole('alertdialog')).toHaveTextContent('Esta acción es definitiva')
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(auth.eliminarCuenta).not.toHaveBeenCalled()
  })

  it('al confirmar elimina la cuenta y lleva al inicio de sesión con un aviso', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderForm(auth)

    await solicitarEliminacion()
    await userEvent.click(screen.getByRole('button', { name: 'Eliminar definitivamente' }))

    expect(auth.eliminarCuenta).toHaveBeenCalledWith('MiClave123')
    expect(await screen.findByRole('status')).toHaveTextContent(MENSAJE_CUENTA_ELIMINADA)
  })

  it('una contraseña incorrecta se muestra en el campo y cierra el diálogo', async () => {
    const auth = crearAuthValue({
      user: usuarioComun,
      token: 't',
      eliminarCuenta: vi.fn().mockRejectedValue(errorHttp(400, 'La contraseña es incorrecta.')),
    })
    renderForm(auth)

    await solicitarEliminacion()
    await userEvent.click(screen.getByRole('button', { name: 'Eliminar definitivamente' }))

    expect(await screen.findByText('La contraseña es incorrecta.')).toBeInTheDocument()
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })

  it.each([
    [errorHttp(409, 'Espera a que termine el análisis en curso antes de eliminar tu cuenta.'), 'análisis en curso'],
    [errorHttp(400, 'No puedes eliminar tu cuenta porque eres el único administrador activo.'), 'único administrador'],
    [errorHttp(429), 'demasiados intentos'],
    [errorHttp(500, 'Internal Server Error'), 'No fue posible eliminar tu cuenta'],
  ])('explica en el diálogo por qué no se pudo eliminar (%#)', async (error, texto) => {
    const auth = crearAuthValue({
      user: usuarioComun,
      token: 't',
      eliminarCuenta: vi.fn().mockRejectedValue(error),
    })
    renderForm(auth)

    await solicitarEliminacion()
    await userEvent.click(screen.getByRole('button', { name: 'Eliminar definitivamente' }))

    const dialogo = screen.getByRole('alertdialog')
    expect(await screen.findByRole('alert')).toHaveTextContent(new RegExp(texto))
    expect(dialogo).toBeInTheDocument()
  })
})
