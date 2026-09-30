import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('@/api/auth', () => ({
  authApi: { login: vi.fn(), register: vi.fn(), logout: vi.fn(), me: vi.fn() },
}))

describe('App', () => {
  it('el aviso de privacidad es accesible sin sesión', async () => {
    window.history.pushState({}, '', '/aviso-privacidad')
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Aviso de privacidad de PrivApp' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '1. ¿Quién es responsable de sus datos?' })).toBeInTheDocument()
  })

  it('una pantalla protegida sin sesión lleva al inicio de sesión', async () => {
    window.history.pushState({}, '', '/historial')
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeInTheDocument()
  })

  it.each(['/login', '/registro', '/aviso-privacidad'])(
    'el pie de página con el enlace al aviso aparece en %s',
    async (ruta) => {
      window.history.pushState({}, '', ruta)
      render(<App />)

      const enlace = await screen.findByRole('link', { name: 'Aviso de privacidad' })
      expect(enlace.closest('footer')).not.toBeNull()
      expect(enlace).toHaveAttribute('href', '/aviso-privacidad')
    },
  )

  it('el glosario es accesible sin sesión y desde el pie de página', async () => {
    window.history.pushState({}, '', '/glosario')
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Glosario' })).toBeInTheDocument()
    const pie = screen.getByRole('navigation', { name: 'Enlaces del pie de página' })
    expect(within(pie).getByRole('link', { name: 'Glosario' })).toHaveAttribute('href', '/glosario')
  })
})
