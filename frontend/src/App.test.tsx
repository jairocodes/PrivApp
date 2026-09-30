import { render, screen } from '@testing-library/react'
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
    expect(screen.getByText('PENDIENTE_CONTENIDO')).toBeInTheDocument()
  })

  it('una pantalla protegida sin sesión lleva al inicio de sesión', async () => {
    window.history.pushState({}, '', '/historial')
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeInTheDocument()
  })
})
