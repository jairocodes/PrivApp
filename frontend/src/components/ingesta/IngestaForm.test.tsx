import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import apiClient from '@/api/client'
import { analisisApi } from '@/api/analisis'
import IngestaForm from './IngestaForm'

vi.mock('@/api/client', () => ({ default: { post: vi.fn() } }))
vi.mock('@/api/analisis', () => ({ analisisApi: { iniciar: vi.fn() } }))

const TEXTO_VALIDO = 'Política de privacidad de ejemplo. '.repeat(10)

function renderIngesta() {
  render(
    <MemoryRouter initialEntries={['/analizar']}>
      <Routes>
        <Route path="/analizar" element={<IngestaForm />} />
        <Route path="/resultados/:id" element={<p>Pantalla de resultados</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function escribirTexto(texto: string) {
  fireEvent.change(screen.getByPlaceholderText(/Pega aquí el texto completo/), {
    target: { value: texto },
  })
}

describe('IngestaForm', () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: { texto_procesado: 'texto normalizado', palabras: 50, fuente: 'texto_directo' },
    })
    vi.mocked(analisisApi.iniciar).mockResolvedValue({
      data: { id_analisis: '5', estado: 'procesando' },
    } as Awaited<ReturnType<typeof analisisApi.iniciar>>)
  })

  it('no permite enviar un texto por debajo del mínimo', () => {
    renderIngesta()
    escribirTexto('Texto demasiado corto')

    expect(screen.getByText('(mínimo 200)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analizar política' })).toBeDisabled()
  })

  it('ingesta el texto, inicia el análisis y navega a los resultados', async () => {
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(apiClient.post).toHaveBeenCalledWith('/api/ingesta/texto', { texto: TEXTO_VALIDO })
    expect(analisisApi.iniciar).toHaveBeenCalledWith('texto normalizado')
    expect(await screen.findByText('Pantalla de resultados')).toBeInTheDocument()
  })

  it('exige una dirección en la pestaña de URL', async () => {
    renderIngesta()
    await userEvent.click(screen.getByRole('tab', { name: 'Desde URL' }))

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(screen.getByText('Por favor ingresa una URL válida.')).toBeInTheDocument()
    expect(apiClient.post).not.toHaveBeenCalled()
  })

  it('muestra el detalle de error que devuelve el servidor', async () => {
    vi.mocked(apiClient.post).mockRejectedValue({
      response: { data: { detail: 'El texto es demasiado corto para analizarlo.' } },
    })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(await screen.findByText('El texto es demasiado corto para analizarlo.')).toBeInTheDocument()
    expect(analisisApi.iniciar).not.toHaveBeenCalled()
  })

  it('explica el límite de intentos ante un 429', async () => {
    vi.mocked(apiClient.post).mockRejectedValue({ response: { status: 429, data: { error: 'Rate limit exceeded' } } })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(await screen.findByText('Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.')).toBeInTheDocument()
  })

  it('exige 40 palabras aunque el texto supere los 200 caracteres', async () => {
    renderIngesta()
    escribirTexto('a'.repeat(250))

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(screen.getByText('El texto debe tener al menos 200 caracteres y 40 palabras.')).toBeInTheDocument()
    expect(apiClient.post).not.toHaveBeenCalled()
  })

  it('no falla si el servidor devuelve la lista de errores de validación', async () => {
    vi.mocked(apiClient.post).mockRejectedValue({
      response: { status: 422, data: { detail: [{ loc: ['body', 'texto'], msg: 'error' }] } },
    })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(await screen.findByText('Ocurrió un error. Intenta de nuevo.')).toBeInTheDocument()
  })
})
