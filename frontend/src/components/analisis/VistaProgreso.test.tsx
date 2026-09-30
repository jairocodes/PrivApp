import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { CONSEJOS_PRIVACIDAD } from '@/data/consejosPrivacidad'
import VistaProgreso from './VistaProgreso'

describe('VistaProgreso', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('indica que se prepara el análisis cuando aún no hay total de secciones', () => {
    render(<VistaProgreso seccionActual={0} seccionesTotal={null} />)
    expect(screen.getByText('Preparando el análisis...')).toBeInTheDocument()
    expect(screen.getByRole('status', { name: 'Analizando' })).toBeInTheDocument()
  })

  it('muestra la sección actual y el total', () => {
    render(<VistaProgreso seccionActual={2} seccionesTotal={4} />)
    expect(screen.getByText('Analizando la política: 2 de 4 secciones listas...')).toBeInTheDocument()
  })

  it('rota los consejos de privacidad mientras espera', () => {
    render(<VistaProgreso seccionActual={1} seccionesTotal={4} />)
    expect(screen.getByText(CONSEJOS_PRIVACIDAD[0])).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(6000)
    })

    expect(screen.getByText(CONSEJOS_PRIVACIDAD[1])).toBeInTheDocument()
  })
})
