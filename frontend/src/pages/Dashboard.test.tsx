import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { crearAuthValue, usuarioComun } from '@/test/fixtures'
import Dashboard from './Dashboard'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))
vi.mock('@/components/dashboard/PanelEstadistico', () => ({ default: () => <p>Panel estadístico</p> }))

describe('Dashboard', () => {
  it('saluda, ofrece las acciones principales e incluye el panel estadístico', () => {
    render(
      <AuthContext.Provider value={crearAuthValue({ user: usuarioComun, token: 't' })}>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </AuthContext.Provider>,
    )

    expect(screen.getByRole('heading', { name: 'Bienvenido, Ana' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Analizar política/ })).toHaveAttribute('href', '/analizar')
    expect(screen.getByText('Pega el texto, ingresa una URL o carga un archivo')).toBeInTheDocument()
    expect(screen.getByText('Panel estadístico')).toBeInTheDocument()
  })
})
