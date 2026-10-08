import { render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { TemaProvider } from '@/context/TemaContext'
import { crearAuthValue, usuarioComun } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import AppLayout from './AppLayout'

function renderLayout(auth: AuthContextValue, ruta: string) {
  render(
    <TemaProvider>
      <AuthContext.Provider value={auth}>
        <MemoryRouter initialEntries={[ruta]}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="*" element={<main><h1>Contenido</h1></main>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </TemaProvider>,
  )
}

const pestanas = () => screen.getByRole('navigation', { name: 'Navegación principal' })

describe('AppLayout', () => {
  it('muestra la página dentro de la barra superior y el pie de página', () => {
    renderLayout(crearAuthValue(), '/glosario')

    expect(screen.getByRole('heading', { name: 'Contenido' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'PrivApp' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Enlaces del pie de página' })).toBeInTheDocument()
  })

  it('ofrece un enlace para saltar al contenido', () => {
    renderLayout(crearAuthValue(), '/glosario')
    expect(screen.getByRole('link', { name: 'Saltar al contenido' })).toHaveAttribute('href', '#contenido')
  })

  it('sin sesión no muestra las pestañas inferiores', () => {
    renderLayout(crearAuthValue(), '/glosario')
    expect(screen.queryByRole('navigation', { name: 'Navegación principal' })).not.toBeInTheDocument()
  })

  it('con sesión muestra las cinco pestañas con su texto', () => {
    renderLayout(crearAuthValue({ user: usuarioComun, token: 't' }), '/dashboard')

    const enlaces = within(pestanas()).getAllByRole('link')
    expect(enlaces.map((e) => e.textContent)).toEqual(['Inicio', 'Analizar', 'Historial', 'Glosario', 'Perfil'])
    expect(within(pestanas()).getByRole('link', { name: 'Perfil' })).toHaveAttribute('href', '/perfil')
  })

  it.each([
    ['/dashboard', 'Inicio'],
    ['/analizar', 'Analizar'],
    ['/resultados/12', 'Analizar'],
    ['/historial', 'Historial'],
    ['/glosario', 'Glosario'],
    ['/perfil', 'Perfil'],
  ])('en %s marca la pestaña %s como la actual', (ruta, actual) => {
    renderLayout(crearAuthValue({ user: usuarioComun, token: 't' }), ruta)

    const marcadas = within(pestanas())
      .getAllByRole('link')
      .filter((e) => e.getAttribute('aria-current') === 'page')
    expect(marcadas.map((e) => e.textContent)).toEqual([actual])
  })
})
