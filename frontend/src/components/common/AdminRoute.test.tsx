import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { administrador, crearAuthValue, usuarioComun } from '@/test/fixtures'
import { esAdministrador } from '@/types/auth'
import type { AuthContextValue } from '@/types/auth'
import AdminRoute from './AdminRoute'

function renderConAuth(auth: AuthContextValue) {
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/login" element={<p>Pantalla de inicio de sesión</p>} />
          <Route path="/dashboard" element={<p>Panel principal</p>} />
          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<p>Contenido de administración</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('AdminRoute', () => {
  it('muestra un indicador mientras se verifica la sesión', () => {
    renderConAuth(crearAuthValue({ isLoading: true }))
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('redirige al inicio de sesión sin usuario autenticado', () => {
    renderConAuth(crearAuthValue())
    expect(screen.getByText('Pantalla de inicio de sesión')).toBeInTheDocument()
  })

  it('redirige al panel principal a un usuario común', () => {
    renderConAuth(crearAuthValue({ user: usuarioComun, token: 't' }))
    expect(screen.getByText('Panel principal')).toBeInTheDocument()
    expect(screen.queryByText('Contenido de administración')).not.toBeInTheDocument()
  })

  it('muestra el contenido al administrador', () => {
    renderConAuth(crearAuthValue({ user: administrador, token: 't' }))
    expect(screen.getByText('Contenido de administración')).toBeInTheDocument()
  })
})

describe('esAdministrador', () => {
  it('distingue el rol administrador', () => {
    expect(esAdministrador(administrador)).toBe(true)
    expect(esAdministrador(usuarioComun)).toBe(false)
    expect(esAdministrador(null)).toBe(false)
  })
})
