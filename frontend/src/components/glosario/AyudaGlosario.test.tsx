import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import AyudaGlosario from './AyudaGlosario'

function renderAyuda(termino: string) {
  return render(
    <MemoryRouter>
      <AyudaGlosario termino={termino} />
    </MemoryRouter>,
  )
}

describe('AyudaGlosario', () => {
  it('muestra la definición al pulsar y la oculta al pulsar de nuevo', async () => {
    renderAyuda('Nivel de riesgo')
    const boton = screen.getByRole('button', { name: 'Qué significa «Nivel de riesgo»' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')

    await userEvent.click(boton)

    expect(boton).toHaveAttribute('aria-expanded', 'true')
    const nota = screen.getByRole('note')
    expect(nota).toHaveTextContent('Nivel de riesgo')
    expect(nota).toHaveTextContent('Calificación general de la política: bajo, medio o alto.')
    expect(screen.getByRole('link', { name: 'Ver en el glosario' })).toHaveAttribute(
      'href',
      '/glosario#nivel-de-riesgo',
    )

    await userEvent.click(boton)
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  it('Escape cierra la definición', async () => {
    renderAyuda('Jurisdicción')
    await userEvent.click(screen.getByRole('button'))
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  it('encuentra el término sin distinguir mayúsculas ni acentos', () => {
    renderAyuda('transferencia de datos a TERCEROS')
    expect(screen.getByRole('button', { name: 'Qué significa «Transferencia de datos a terceros»' })).toBeInTheDocument()
  })

  it('no muestra nada para un término que no está en el glosario', () => {
    const { container } = renderAyuda('Término inexistente')
    expect(container).toBeEmptyDOMElement()
  })
})
