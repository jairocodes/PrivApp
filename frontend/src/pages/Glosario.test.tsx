import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { GLOSARIO } from '@/data/glosario'
import Glosario from './Glosario'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))

function renderGlosario() {
  render(
    <MemoryRouter>
      <Glosario />
    </MemoryRouter>,
  )
}

describe('Glosario', () => {
  it('muestra todos los términos con su definición', () => {
    renderGlosario()

    expect(screen.getByRole('heading', { name: 'Glosario' })).toBeInTheDocument()
    expect(screen.getByText(`${GLOSARIO.length} términos`)).toBeInTheDocument()
    expect(screen.getByText('Transferencia de datos a terceros')).toBeInTheDocument()
    expect(screen.queryByText('PENDIENTE_CONTENIDO')).not.toBeInTheDocument()
    expect(
      screen.getByText('Categoría para los hallazgos que no corresponden a ninguno de los demás tipos de tratamiento de datos.'),
    ).toBeInTheDocument()
  })

  it('cada término tiene un ancla para enlazarlo desde los resultados', () => {
    const { container } = render(
      <MemoryRouter>
        <Glosario />
      </MemoryRouter>,
    )
    expect(container.querySelector('#nivel-de-riesgo')).toHaveTextContent('Nivel de riesgo')
  })

  it('la búsqueda filtra sin distinguir mayúsculas ni acentos', async () => {
    renderGlosario()

    await userEvent.type(screen.getByRole('searchbox', { name: 'Buscar un término' }), 'JURISDICCION')

    expect(screen.getByText('Jurisdicción')).toBeInTheDocument()
    expect(screen.queryByText('Datos personales')).not.toBeInTheDocument()
    expect(screen.getByText('1 término')).toBeInTheDocument()
  })

  it('informa cuando la búsqueda no encuentra términos', async () => {
    renderGlosario()

    await userEvent.type(screen.getByRole('searchbox', { name: 'Buscar un término' }), 'blockchain')

    expect(screen.getByText('No se encontraron términos para «blockchain».')).toBeInTheDocument()
  })

  it('baja hasta el término indicado en la dirección', () => {
    const desplazar = vi.fn()
    Element.prototype.scrollIntoView = desplazar
    render(
      <MemoryRouter initialEntries={['/glosario#jurisdiccion']}>
        <Glosario />
      </MemoryRouter>,
    )

    expect(desplazar).toHaveBeenCalledTimes(1)
    expect(desplazar.mock.contexts[0]).toHaveAttribute('id', 'jurisdiccion')
  })
})
