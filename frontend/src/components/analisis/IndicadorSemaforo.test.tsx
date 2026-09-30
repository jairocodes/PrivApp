import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import IndicadorSemaforo from './IndicadorSemaforo'

describe('IndicadorSemaforo', () => {
  it.each([
    ['bajo', 'Riesgo Bajo'],
    ['medio', 'Riesgo Medio'],
    ['alto', 'Riesgo Alto'],
  ] as const)('muestra la etiqueta textual del nivel %s', (nivel, etiqueta) => {
    render(<IndicadorSemaforo nivel={nivel} />)
    expect(screen.getByText(etiqueta)).toBeInTheDocument()
  })

  it('no depende solo del color: el punto es decorativo', () => {
    const { container } = render(<IndicadorSemaforo nivel="alto" />)
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeNull()
  })

  it('agrega la descripción del nivel cuando mostrarTexto está activo', () => {
    render(<IndicadorSemaforo nivel="medio" mostrarTexto />)
    expect(screen.getByText('Riesgo Medio')).toBeInTheDocument()
    expect(screen.getByText(/merecen atención antes de aceptar/)).toBeInTheDocument()
  })

  it('usa la paleta semántica de riesgo', () => {
    render(<IndicadorSemaforo nivel="bajo" />)
    expect(screen.getByText('Riesgo Bajo')).toHaveClass('text-riesgo-bajo')
  })
})
