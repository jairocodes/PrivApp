import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/AuthContext'
import { crearAuthValue } from '@/test/fixtures'
import type { AuthContextValue } from '@/types/auth'
import RegisterForm from './RegisterForm'

function renderRegistro(auth: AuthContextValue) {
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={['/registro']}>
        <Routes>
          <Route path="/registro" element={<RegisterForm />} />
          <Route path="/dashboard" element={<p>Panel principal</p>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

async function completar(datos: {
  nombre: string
  email: string
  password: string
  confirmacion: string
  aceptaAviso?: boolean
  declaraEdad?: boolean
}) {
  await userEvent.type(screen.getByLabelText('Nombre completo'), datos.nombre)
  await userEvent.type(screen.getByLabelText('Correo electrónico'), datos.email)
  await userEvent.type(screen.getByLabelText('Contraseña'), datos.password)
  await userEvent.type(screen.getByLabelText('Confirmar contraseña'), datos.confirmacion)
  if (datos.aceptaAviso ?? true) {
    await userEvent.click(screen.getByRole('checkbox', { name: /acepto el aviso de privacidad/ }))
  }
  if (datos.declaraEdad ?? true) {
    await userEvent.click(screen.getByRole('checkbox', { name: /mayor de 18 años/ }))
  }
  await userEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))
}

const VALIDOS = {
  nombre: 'Ana López',
  email: 'ana@privapp.test',
  password: 'Segura123',
  confirmacion: 'Segura123',
}

describe('RegisterForm', () => {
  it('valida nombre, correo y fortaleza de la contraseña', async () => {
    const auth = crearAuthValue()
    renderRegistro(auth)

    await completar({ nombre: 'A', email: 'x@privapp.test', password: 'debil', confirmacion: 'debil' })

    expect(screen.getByText('El nombre debe tener al menos 2 caracteres.')).toBeInTheDocument()
    expect(screen.getByText('La contraseña debe tener al menos 8 caracteres.')).toBeInTheDocument()
    expect(auth.register).not.toHaveBeenCalled()
  })

  it('exige que las contraseñas coincidan', async () => {
    const auth = crearAuthValue()
    renderRegistro(auth)

    await completar({ ...VALIDOS, confirmacion: 'Distinta123' })

    expect(screen.getByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(auth.register).not.toHaveBeenCalled()
  })

  it('registra al usuario y navega al panel principal', async () => {
    const auth = crearAuthValue()
    renderRegistro(auth)

    await completar({ ...VALIDOS, nombre: '  Ana López  ' })

    expect(auth.register).toHaveBeenCalledWith('Ana López', 'ana@privapp.test', 'Segura123', true, true)
    expect(await screen.findByText('Panel principal')).toBeInTheDocument()
  })

  it('exige aceptar el aviso de privacidad', async () => {
    const auth = crearAuthValue()
    renderRegistro(auth)

    await completar({ ...VALIDOS, aceptaAviso: false })

    expect(screen.getByText('Debes aceptar el aviso de privacidad para registrarte.')).toBeInTheDocument()
    expect(auth.register).not.toHaveBeenCalled()
  })

  it('exige la declaración de edad o de consentimiento', async () => {
    const auth = crearAuthValue()
    renderRegistro(auth)

    await completar({ ...VALIDOS, declaraEdad: false })

    expect(screen.getByText('Debes declarar que eres mayor de 18 años o que cuentas con el consentimiento de tu madre, padre o persona encargada.')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /mayor de 18 años/ })).toHaveAttribute('aria-invalid', 'true')
    expect(auth.register).not.toHaveBeenCalled()
  })

  it('enlaza al aviso de privacidad desde la casilla', () => {
    renderRegistro(crearAuthValue())

    expect(screen.getByRole('link', { name: 'aviso de privacidad' })).toHaveAttribute(
      'href',
      '/aviso-privacidad',
    )
  })

  it('avisa si el correo ya está registrado (409)', async () => {
    const auth = crearAuthValue({
      register: vi.fn().mockRejectedValue({ response: { status: 409 } }),
    })
    renderRegistro(auth)

    await completar(VALIDOS)

    expect(await screen.findByText('Este correo ya está registrado.')).toBeInTheDocument()
  })

  it('explica el límite de intentos ante un 429', async () => {
    const auth = crearAuthValue({
      register: vi.fn().mockRejectedValue({ response: { status: 429 } }),
    })
    renderRegistro(auth)

    await completar(VALIDOS)

    expect(await screen.findByRole('alert')).toHaveTextContent('Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.')
  })
})
