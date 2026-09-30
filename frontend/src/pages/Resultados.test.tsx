import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { analisisApi } from '@/api/analisis'
import { useAnalisis } from '@/hooks/useAnalisis'
import { useProgresoAnalisis } from '@/hooks/useProgresoAnalisis'
import { analisisEjemplo } from '@/test/fixtures'
import Resultados from './Resultados'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))
vi.mock('@/hooks/useAnalisis', () => ({ useAnalisis: vi.fn() }))
vi.mock('@/hooks/useProgresoAnalisis', () => ({ useProgresoAnalisis: vi.fn() }))
vi.mock('@/api/analisis', () => ({ analisisApi: { descargarPDF: vi.fn() } }))

const obtener = vi.fn()

function renderResultados() {
  render(
    <MemoryRouter initialEntries={['/resultados/7']}>
      <Routes>
        <Route path="/resultados/:id" element={<Resultados />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Resultados', () => {
  beforeEach(() => {
    vi.mocked(useAnalisis).mockReturnValue({ resultado: null, isLoading: false, error: null, obtener })
  })

  it('muestra la vista de progreso mientras el análisis se procesa', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'procesando', seccionActual: 1, seccionesTotal: 3 })
    renderResultados()

    expect(screen.getByText('Analizando sección 1 de 3...')).toBeInTheDocument()
    expect(obtener).not.toHaveBeenCalled()
  })

  it('muestra un mensaje si el análisis terminó con error', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'error', seccionActual: 0, seccionesTotal: null })
    renderResultados()

    expect(screen.getByText('Ocurrió un error durante el análisis. Intenta nuevamente.')).toBeInTheDocument()
  })

  it('pide el resultado al completarse el análisis', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 3, seccionesTotal: 3 })
    renderResultados()

    expect(obtener).toHaveBeenCalledWith('7')
  })

  it('presenta el panel con puntaje accesible, secciones y recomendaciones', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 1, seccionesTotal: 1 })
    vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisEjemplo, isLoading: false, error: null, obtener })
    renderResultados()

    expect(
      screen.getByRole('img', { name: 'Puntaje de riesgo: 90 de 100, Riesgo Alto' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Esta política presenta 1 hallazgo(s) de riesgo alto.')).toBeInTheDocument()
    expect(screen.getByText('Compartición con terceros')).toBeInTheDocument()
    expect(screen.getByText('Revisa con quién se comparten tus datos.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Descargar PDF/ })).toBeInTheDocument()
  })

  it('explica el límite de descargas del PDF ante un 429', async () => {
    vi.mocked(analisisApi.descargarPDF).mockRejectedValue({ response: { status: 429 } })
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 1, seccionesTotal: 1 })
    vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisEjemplo, isLoading: false, error: null, obtener })
    renderResultados()

    await userEvent.click(screen.getByRole('button', { name: /Descargar PDF/ }))

    expect(await screen.findByText('Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.')).toBeInTheDocument()
  })

  it('ofrece ayuda del glosario para el nivel y el puntaje de riesgo', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 1, seccionesTotal: 1 })
    vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisEjemplo, isLoading: false, error: null, obtener })
    renderResultados()

    expect(screen.getByRole('button', { name: 'Qué significa «Nivel de riesgo»' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Qué significa «Puntaje de riesgo»' })).toBeInTheDocument()
  })
})
