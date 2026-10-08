import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import BotonTema from '@/components/common/BotonTema'
import { CLAVE_TEMA, TemaProvider } from '@/context/TemaContext'
import { useTema } from '@/hooks/useTema'

// Simula prefers-color-scheme del dispositivo y permite cambiarlo en la prueba.
function simularSistema(oscuro: boolean) {
  const oyentes = new Set<(e: MediaQueryListEvent) => void>()
  const consulta = {
    matches: oscuro,
    addEventListener: (_: string, fn: (e: MediaQueryListEvent) => void) => oyentes.add(fn),
    removeEventListener: (_: string, fn: (e: MediaQueryListEvent) => void) => oyentes.delete(fn),
  }
  vi.stubGlobal('matchMedia', vi.fn(() => consulta))
  return (nuevo: boolean) => {
    consulta.matches = nuevo
    oyentes.forEach((fn) => fn({ matches: nuevo } as MediaQueryListEvent))
  }
}

function Estado() {
  const { preferencia, oscuro } = useTema()
  return <p>{`${preferencia}:${oscuro ? 'oscuro' : 'claro'}`}</p>
}

function renderTema() {
  render(
    <TemaProvider>
      <Estado />
      <BotonTema />
    </TemaProvider>,
  )
}

const esOscuro = () => document.documentElement.classList.contains('dark')

describe('TemaProvider', () => {
  beforeEach(() => document.documentElement.classList.remove('dark'))
  afterEach(() => vi.unstubAllGlobals())

  it('sin preferencia guardada sigue al sistema', () => {
    simularSistema(true)
    renderTema()

    expect(screen.getByText('sistema:oscuro')).toBeInTheDocument()
    expect(esOscuro()).toBe(true)
  })

  it('sigue los cambios del sistema mientras no haya preferencia', () => {
    const cambiarSistema = simularSistema(false)
    renderTema()
    expect(esOscuro()).toBe(false)

    act(() => cambiarSistema(true))

    expect(screen.getByText('sistema:oscuro')).toBeInTheDocument()
    expect(esOscuro()).toBe(true)
  })

  it('una preferencia guardada manda sobre el sistema', () => {
    simularSistema(true)
    localStorage.setItem(CLAVE_TEMA, 'claro')
    renderTema()

    expect(screen.getByText('claro:claro')).toBeInTheDocument()
    expect(esOscuro()).toBe(false)
  })

  it('el botón alterna el modo, lo aplica y lo recuerda', async () => {
    simularSistema(false)
    renderTema()
    const boton = screen.getByRole('button', { name: 'Modo oscuro' })
    expect(boton).toHaveAttribute('aria-pressed', 'false')

    await userEvent.click(boton)

    expect(boton).toHaveAttribute('aria-pressed', 'true')
    expect(esOscuro()).toBe(true)
    expect(localStorage.getItem(CLAVE_TEMA)).toBe('oscuro')

    await userEvent.click(boton)

    expect(esOscuro()).toBe(false)
    expect(localStorage.getItem(CLAVE_TEMA)).toBe('claro')
  })

  it('funciona aunque el navegador no informe el tema del sistema', () => {
    vi.stubGlobal('matchMedia', undefined)
    renderTema()

    expect(screen.getByText('sistema:claro')).toBeInTheDocument()
  })

  it('useTema exige estar dentro del proveedor', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Estado />)).toThrow('useTema debe usarse dentro de <TemaProvider>')
  })
})
