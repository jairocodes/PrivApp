import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { analisisApi } from '@/api/analisis'
import type { EstadisticasPersonales } from '@/types/analisis'
import PanelEstadistico from './PanelEstadistico'

vi.mock('@/api/analisis', () => ({ analisisApi: { estadisticas: vi.fn() } }))
// El gráfico de recharts necesita medir el contenedor, algo que jsdom no hace.
vi.mock('@/components/dashboard/GraficoDistribucion', () => ({
  default: ({ distribucion }: { distribucion: EstadisticasPersonales['por_nivel'] }) => (
    <div data-testid="grafico">{JSON.stringify(distribucion)}</div>
  ),
}))

function responder(datos: EstadisticasPersonales) {
  vi.mocked(analisisApi.estadisticas).mockResolvedValue({
    data: datos,
  } as Awaited<ReturnType<typeof analisisApi.estadisticas>>)
}

describe('PanelEstadistico', () => {
  it('muestra el total, el promedio y la distribución por nivel', async () => {
    responder({ total: 4, por_nivel: { bajo: 1, medio: 1, alto: 2 }, puntaje_promedio: 55.3 })
    render(<PanelEstadistico />)

    expect(await screen.findByText('4')).toBeInTheDocument()
    expect(screen.getByText('Análisis realizados')).toBeInTheDocument()
    expect(screen.getByText('55.3/100')).toBeInTheDocument()
    const leyenda = screen.getByRole('list', { name: 'Análisis por nivel de riesgo' })
    expect(within(leyenda).getByText('Bajo: 1')).toBeInTheDocument()
    expect(within(leyenda).getByText('Alto: 2')).toBeInTheDocument()
    expect(await screen.findByTestId('grafico')).toHaveTextContent('"alto":2')
  })

  it('sin análisis muestra ceros y una indicación, sin gráfico', async () => {
    responder({ total: 0, por_nivel: { bajo: 0, medio: 0, alto: 0 }, puntaje_promedio: 0 })
    render(<PanelEstadistico />)

    expect(await screen.findByText(/Aún no tienes análisis/)).toBeInTheDocument()
    expect(screen.getByText('0/100')).toBeInTheDocument()
    expect(screen.getByText('Medio: 0')).toBeInTheDocument()
    expect(screen.queryByTestId('grafico')).not.toBeInTheDocument()
  })

  it('muestra un error si no se pueden cargar', async () => {
    vi.mocked(analisisApi.estadisticas).mockRejectedValue(new Error('red'))
    render(<PanelEstadistico />)

    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar tus estadísticas.')
  })
})
