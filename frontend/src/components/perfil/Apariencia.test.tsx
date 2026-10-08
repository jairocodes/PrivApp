import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { CLAVE_TEMA, TemaProvider } from '@/context/TemaContext'
import Apariencia from './Apariencia'

function renderApariencia() {
  render(
    <TemaProvider>
      <Apariencia />
    </TemaProvider>,
  )
}

describe('Apariencia', () => {
  beforeEach(() => document.documentElement.classList.remove('dark'))
  afterEach(() => document.documentElement.classList.remove('dark'))

  it('por defecto sigue al dispositivo', () => {
    renderApariencia()
    expect(screen.getByRole('group', { name: 'Apariencia' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Automático' })).toBeChecked()
  })

  it('elegir Oscuro lo aplica y lo recuerda; Automático olvida la elección', async () => {
    renderApariencia()

    await userEvent.click(screen.getByRole('radio', { name: 'Oscuro' }))
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem(CLAVE_TEMA)).toBe('oscuro')

    await userEvent.click(screen.getByRole('radio', { name: 'Automático' }))
    expect(localStorage.getItem(CLAVE_TEMA)).toBeNull()
  })
})
