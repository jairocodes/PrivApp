import { render, screen } from '@testing-library/react'
import { beforeAll, describe, expect, it } from 'vitest'
import GraficoDistribucion from './GraficoDistribucion'

beforeAll(() => {
  // jsdom no implementa ResizeObserver, que usa ResponsiveContainer de recharts.
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
})

describe('GraficoDistribucion', () => {
  it('describe la distribución en texto para lectores de pantalla', () => {
    render(<GraficoDistribucion distribucion={{ bajo: 1, medio: 0, alto: 3 }} />)

    expect(
      screen.getByRole('img', {
        name: 'Distribución por nivel de riesgo: 1 de riesgo bajo, 0 de riesgo medio, 3 de riesgo alto',
      }),
    ).toBeInTheDocument()
  })
})
