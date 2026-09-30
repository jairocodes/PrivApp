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
})
