import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { crearAuthValue } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import ProtectedRoute from './ProtectedRoute'

function renderConAuth(auth: AuthContextValue) {
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={['/privado']}>
        <Routes>
          <Route path="/login" element={<p>Pantalla de inicio de sesión</p>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/privado" element={<p>Contenido protegido</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('ProtectedRoute', () => {
  it('muestra un indicador mientras se verifica la sesión', () => {
    renderConAuth(crearAuthValue({ isLoading: true }))
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('redirige al inicio de sesión sin usuario autenticado', () => {
    renderConAuth(crearAuthValue())
    expect(screen.getByText('Pantalla de inicio de sesión')).toBeInTheDocument()
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument()
  })

  it('muestra el contenido cuando hay usuario autenticado', () => {
    renderConAuth(
      crearAuthValue({ user: { id: 1, nombre: 'Ana', email: 'ana@privapp.test', role: 'usuario' }, token: 't' }),
    )
    expect(screen.getByText('Contenido protegido')).toBeInTheDocument()
  })
})
