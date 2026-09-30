import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { seccionEjemplo } from '@/test/fixtures'
import TarjetaSeccion from './TarjetaSeccion'

describe('TarjetaSeccion', () => {
  it('muestra título, categoría y el nivel máximo de sus hallazgos', () => {
    render(<TarjetaSeccion seccion={seccionEjemplo} indice={1} />)
    expect(screen.getByText('Compartición con terceros')).toBeInTheDocument()
    expect(screen.getByText('Third Party Sharing/Collection')).toBeInTheDocument()
    expect(screen.getByText('Riesgo Alto')).toBeInTheDocument()
  })

  it('está contraída por defecto y se expande al pulsarla', async () => {
    render(<TarjetaSeccion seccion={seccionEjemplo} indice={1} />)
    const boton = screen.getByRole('button', { expanded: false })
    expect(screen.queryByText('Hallazgos (2)')).not.toBeInTheDocument()

    await userEvent.click(boton)

    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Hallazgos (2)')).toBeInTheDocument()
  })

  it('muestra hallazgos y fuentes normativas cuando está expandida', () => {
    render(<TarjetaSeccion seccion={seccionEjemplo} indice={1} inicialmenteExpandida />)
    expect(screen.getByText('Tus datos pueden llegar a empresas que no conoces.')).toBeInTheDocument()
    expect(screen.getByText('RGPD')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'riesgo' })).toBeInTheDocument()
  })

  it('avisa cuando una sección no tiene hallazgos', () => {
    render(
      <TarjetaSeccion seccion={{ ...seccionEjemplo, hallazgos: [] }} indice={2} inicialmenteExpandida />,
    )
    expect(screen.getByText('No se identificaron hallazgos en esta sección.')).toBeInTheDocument()
  })

  it('muestra el tipo de tratamiento de cada hallazgo', () => {
    render(<TarjetaSeccion seccion={seccionEjemplo} indice={1} inicialmenteExpandida />)

    const etiqueta = screen.getByText('Transferencia de datos a terceros')
    expect(etiqueta).toHaveAttribute('title', 'Tipo de tratamiento de datos')
    expect(etiqueta).toHaveTextContent('Tipo de tratamiento: Transferencia de datos a terceros')
  })

  it('los hallazgos de análisis antiguos se muestran sin etiqueta y sin errores', () => {
    render(<TarjetaSeccion seccion={seccionEjemplo} indice={1} inicialmenteExpandida />)

    // El segundo hallazgo del ejemplo no tiene tipo de tratamiento (análisis antiguo).
    expect(screen.getByText('Se identifica al responsable del tratamiento.')).toBeInTheDocument()
    expect(screen.getAllByTitle('Tipo de tratamiento de datos')).toHaveLength(1)
  })

  it('ofrece la definición del tipo de tratamiento desde el glosario', async () => {
    render(<TarjetaSeccion seccion={seccionEjemplo} indice={1} inicialmenteExpandida />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Qué significa «Transferencia de datos a terceros»' }),
    )

    expect(screen.getByRole('link', { name: 'Ver en el glosario' })).toHaveAttribute(
      'href',
      '/glosario#transferencia-de-datos-a-terceros',
    )
  })
})
