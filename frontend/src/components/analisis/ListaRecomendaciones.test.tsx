import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ListaRecomendaciones from './ListaRecomendaciones'

describe('ListaRecomendaciones', () => {
  it('no renderiza nada sin recomendaciones', () => {
    const { container } = render(<ListaRecomendaciones recomendaciones={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('muestra las recomendaciones numeradas en orden', () => {
    render(<ListaRecomendaciones recomendaciones={['Primera', 'Segunda']} />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(within(items[0]).getByText('1')).toBeInTheDocument()
    expect(items[0]).toHaveTextContent('Primera')
    expect(items[1]).toHaveTextContent('Segunda')
  })
})
