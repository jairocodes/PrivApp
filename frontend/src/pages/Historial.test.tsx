import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { analisisApi } from '@/api/analisis'
import type { AnalisisHistorialItem, HistorialResponse } from '@/types/analisis'
import Historial from './Historial'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))
vi.mock('@/api/analisis', () => ({ analisisApi: { listar: vi.fn() } }))

const ITEM: AnalisisHistorialItem = {
  id_analisis: '12',
  fecha: '2026-09-01T15:30:00Z',
  nivel_riesgo_global: 'medio',
  puntaje: 40,
  comentario_breve: 'Se detectaron 2 hallazgo(s) de riesgo medio.',
}

function responderListado(parcial: Partial<HistorialResponse>) {
  vi.mocked(analisisApi.listar).mockResolvedValue({
    data: { items: [], total: 0, page: 1, page_size: 10, ...parcial },
  } as Awaited<ReturnType<typeof analisisApi.listar>>)
}

function renderHistorial() {
  render(
    <MemoryRouter>
      <Historial />
    </MemoryRouter>,
  )
}

describe('Historial', () => {
  it('invita a analizar cuando el usuario no tiene análisis', async () => {
    responderListado({})
    renderHistorial()

    expect(await screen.findByText('Aún no tienes análisis registrados.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Analizar una política' })).toHaveAttribute('href', '/analizar')
    expect(analisisApi.listar).toHaveBeenCalledWith(1, 10, {})
  })

  it('lista los análisis con su nivel de riesgo y enlace al detalle', async () => {
    responderListado({ items: [ITEM], total: 1 })
    renderHistorial()

    expect(await screen.findByText(ITEM.comentario_breve)).toBeInTheDocument()
    expect(screen.getByText('Riesgo Medio')).toBeInTheDocument()
    expect(screen.getByText('40')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Se detectaron 2 hallazgo/ })).toHaveAttribute(
      'href',
      '/resultados/12',
    )
  })

  it('muestra un mensaje si no se puede cargar el historial', async () => {
    vi.mocked(analisisApi.listar).mockRejectedValue(new Error('red'))
    renderHistorial()

    expect(await screen.findByText('No fue posible cargar el historial de análisis.')).toBeInTheDocument()
  })

  it('pagina los resultados', async () => {
    responderListado({ items: [ITEM], total: 15 })
    renderHistorial()

    expect(await screen.findByText('Página 1 de 2')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()

    responderListado({ items: [{ ...ITEM, id_analisis: '13' }], total: 15, page: 2 })
    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(await screen.findByText('Página 2 de 2')).toBeInTheDocument()
    expect(analisisApi.listar).toHaveBeenLastCalledWith(2, 10, {})
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled()
  })
})
