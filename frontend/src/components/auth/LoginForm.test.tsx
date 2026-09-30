import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { crearAuthValue } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import LoginForm from './LoginForm'

function renderLogin(auth: AuthContextValue) {
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route path="/dashboard" element={<p>Panel principal</p>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

async function completar(email: string, password: string) {
  await userEvent.type(screen.getByLabelText('Correo electrónico'), email)
  await userEvent.type(screen.getByLabelText('Contraseña'), password)
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
}

describe('LoginForm', () => {
  it('exige correo y contraseña antes de enviar', async () => {
    const auth = crearAuthValue()
    renderLogin(auth)

    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(screen.getByText('El correo es obligatorio.')).toBeInTheDocument()
    expect(screen.getByText('La contraseña es obligatoria.')).toBeInTheDocument()
    expect(auth.login).not.toHaveBeenCalled()
  })

  it('inicia sesión y navega al panel principal', async () => {
    const auth = crearAuthValue()
    renderLogin(auth)

    await completar('ana@privapp.test', 'Segura123')

    expect(auth.login).toHaveBeenCalledWith('ana@privapp.test', 'Segura123')
    expect(await screen.findByText('Panel principal')).toBeInTheDocument()
  })

  it('informa credenciales incorrectas ante un 401', async () => {
    const auth = crearAuthValue({
      login: vi.fn().mockRejectedValue({ response: { status: 401 } }),
    })
    renderLogin(auth)

    await completar('ana@privapp.test', 'Incorrecta1')

    expect(await screen.findByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos.')
  })

  it('muestra un error genérico ante otros fallos', async () => {
    const auth = crearAuthValue({
      login: vi.fn().mockRejectedValue({ response: { status: 500 } }),
    })
    renderLogin(auth)

    await completar('ana@privapp.test', 'Segura123')

    expect(await screen.findByRole('alert')).toHaveTextContent('Ocurrió un error. Intenta nuevamente.')
  })

  it('explica el límite de intentos ante un 429', async () => {
    const auth = crearAuthValue({
      login: vi.fn().mockRejectedValue({ response: { status: 429 } }),
    })
    renderLogin(auth)

    await completar('ana@privapp.test', 'Segura123')

    expect(await screen.findByRole('alert')).toHaveTextContent('Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.')
  })
})
