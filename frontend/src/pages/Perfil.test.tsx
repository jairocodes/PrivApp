import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { TemaProvider } from '@/context/TemaContext'
import { crearAuthValue, usuarioComun } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import Perfil from './Perfil'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))

function renderPerfil(auth: AuthContextValue) {
  render(
    <TemaProvider>
      <AuthContext.Provider value={auth}>
        <MemoryRouter>
          <Perfil />
        </MemoryRouter>
      </AuthContext.Provider>
    </TemaProvider>,
  )
}

async function guardarNombre(nombre: string) {
  const campo = screen.getByLabelText('Nombre completo')
  await userEvent.clear(campo)
  if (nombre) await userEvent.type(campo, nombre)
  await userEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
}

describe('Perfil', () => {
  it('muestra los datos de la cuenta y el correo como no editable', () => {
    renderPerfil(crearAuthValue({ user: usuarioComun, token: 't' }))

    expect(screen.getByText(usuarioComun.email)).toBeInTheDocument()
    expect(screen.getByText('Usuario')).toBeInTheDocument()
    expect(screen.getByText('El correo electrónico no se puede modificar.')).toBeInTheDocument()
    expect(screen.getByLabelText('Nombre completo')).toHaveValue(usuarioComun.nombre)
    expect(screen.queryByRole('textbox', { name: /correo/i })).not.toBeInTheDocument()
  })

  it('ofrece eliminar la cuenta', () => {
    renderPerfil(crearAuthValue({ user: usuarioComun, token: 't' }))
    expect(screen.getByRole('heading', { name: 'Eliminar mi cuenta' })).toBeInTheDocument()
  })

  it('guarda el nombre sin espacios en los extremos y confirma el cambio', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderPerfil(auth)

    await guardarNombre('  Ana María  ')

    expect(auth.actualizarPerfil).toHaveBeenCalledWith('Ana María')
    expect(await screen.findByRole('status')).toHaveTextContent('Tu nombre se actualizó correctamente.')
  })

  it('rechaza un nombre vacío', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderPerfil(auth)

    await guardarNombre('')

    expect(screen.getByText('El nombre debe tener al menos 2 caracteres.')).toBeInTheDocument()
    expect(auth.actualizarPerfil).not.toHaveBeenCalled()
  })

  it('rechaza un nombre de más de 100 caracteres', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderPerfil(auth)

    // maxLength limita la escritura; se simula un valor pegado más largo.
    fireEvent.change(screen.getByLabelText('Nombre completo'), { target: { value: 'x'.repeat(101) } })
    await userEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(screen.getByText('El nombre no puede superar los 100 caracteres.')).toBeInTheDocument()
    expect(auth.actualizarPerfil).not.toHaveBeenCalled()
  })

  it('incluye el formulario de cambio de contraseña', () => {
    renderPerfil(crearAuthValue({ user: usuarioComun, token: 't' }))
    expect(screen.getByRole('heading', { name: 'Cambiar contraseña' })).toBeInTheDocument()
  })

  it('informa si el servidor rechaza el cambio', async () => {
    const auth = crearAuthValue({
      user: usuarioComun,
      token: 't',
      actualizarPerfil: vi.fn().mockRejectedValue(new Error('422')),
    })
    renderPerfil(auth)

    await guardarNombre('Ana María')

    expect(await screen.findByText('No fue posible actualizar tu nombre. Intenta nuevamente.')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
