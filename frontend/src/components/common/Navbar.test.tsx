import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { administrador, crearAuthValue, usuarioComun } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import Navbar from './Navbar'

function renderNavbar(auth: AuthContextValue) {
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('Navbar', () => {
  it('muestra el nombre del usuario y permite cerrar sesión', async () => {
    const auth = crearAuthValue({ user: usuarioComun, token: 't' })
    renderNavbar(auth)

    expect(screen.getByText('Ana')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(auth.logout).toHaveBeenCalled()
  })

  it('enlaza al perfil del usuario', () => {
    renderNavbar(crearAuthValue({ user: usuarioComun, token: 't' }))
    expect(screen.getByRole('link', { name: 'Mi perfil' })).toHaveAttribute('href', '/perfil')
  })

  it('no muestra la administración a un usuario común', () => {
    renderNavbar(crearAuthValue({ user: usuarioComun, token: 't' }))
    expect(screen.queryByRole('link', { name: 'Administración' })).not.toBeInTheDocument()
  })

  it('muestra el enlace de administración al administrador', () => {
    renderNavbar(crearAuthValue({ user: administrador, token: 't' }))
    expect(screen.getByRole('link', { name: 'Administración' })).toHaveAttribute('href', '/admin')
  })

  it('sin sesión solo muestra la marca', () => {
    renderNavbar(crearAuthValue())
    expect(screen.getByRole('link', { name: 'PrivApp' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })
})
