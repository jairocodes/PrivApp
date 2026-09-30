import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { IngestaResponse } from '@/types/ingesta'
import VistaPreviaTexto from './VistaPreviaTexto'

const RESULTADO: IngestaResponse = {
  texto_procesado: 'Recopilamos su nombre y correo.\n\nPuede solicitar la eliminación de sus datos.',
  caracteres: 12345,
  palabras: 2100,
  fuente: 'texto_directo',
}

function renderVista(props: Partial<Parameters<typeof VistaPreviaTexto>[0]> = {}) {
  const handlers = { onConfirmar: vi.fn(), onCorregir: vi.fn(), onCancelar: vi.fn() }
  render(<VistaPreviaTexto resultado={RESULTADO} {...handlers} {...props} />)
  return handlers
}

describe('VistaPreviaTexto', () => {
  it('muestra el texto normalizado con su número de caracteres y palabras', () => {
    renderVista()

    expect(screen.getByRole('heading', { name: 'Revisa el texto antes de analizarlo' })).toBeInTheDocument()
    expect(screen.getByLabelText('Texto que se analizará')).toHaveTextContent('Recopilamos su nombre y correo.')
    expect(screen.getByText('12,345')).toBeInTheDocument()
    expect(screen.getByText('2,100')).toBeInTheDocument()
    expect(screen.getByText('Texto pegado')).toBeInTheDocument()
  })

  it.each([
    ['https://ejemplo.com/privacidad', 'Dirección web: https://ejemplo.com/privacidad'],
    ['politica.pdf', 'Archivo: politica.pdf'],
  ])('describe el origen %s', (fuente, descripcion) => {
    renderVista({ resultado: { ...RESULTADO, fuente } })
    expect(screen.getByText(descripcion)).toBeInTheDocument()
  })

  it('llama a la acción de cada botón', async () => {
    const { onConfirmar, onCorregir, onCancelar } = renderVista()

    await userEvent.click(screen.getByRole('button', { name: 'Confirmar y analizar' }))
    await userEvent.click(screen.getByRole('button', { name: 'Corregir' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(onConfirmar).toHaveBeenCalledTimes(1)
    expect(onCorregir).toHaveBeenCalledTimes(1)
    expect(onCancelar).toHaveBeenCalledTimes(1)
  })

  it('mientras inicia el análisis bloquea las acciones y muestra errores', () => {
    renderVista({ iniciando: true, error: 'No fue posible iniciar el análisis.' })

    expect(screen.getByRole('button', { name: 'Cargando...' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Corregir' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled()
    expect(screen.getByRole('alert')).toHaveTextContent('No fue posible iniciar el análisis.')
  })
})
