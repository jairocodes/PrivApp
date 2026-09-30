import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { analisisApi } from '@/api/analisis'
import { ingestaApi } from '@/api/ingesta'
import IngestaForm from './IngestaForm'

vi.mock('@/api/ingesta', () => ({
  ingestaApi: { enviarTexto: vi.fn(), enviarURL: vi.fn(), enviarArchivo: vi.fn() },
}))
vi.mock('@/api/analisis', () => ({ analisisApi: { iniciar: vi.fn() } }))

const TEXTO_VALIDO = 'Política de privacidad de ejemplo. '.repeat(10)

const ningunaViaLlamada = () =>
  [ingestaApi.enviarTexto, ingestaApi.enviarURL, ingestaApi.enviarArchivo].every(
    (via) => vi.mocked(via).mock.calls.length === 0,
  )

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
    const respuesta = {
      data: { texto_procesado: 'texto normalizado', caracteres: 400, palabras: 50, fuente: 'texto_directo' },
    } as Awaited<ReturnType<typeof ingestaApi.enviarTexto>>
    vi.mocked(ingestaApi.enviarTexto).mockResolvedValue(respuesta)
    vi.mocked(ingestaApi.enviarURL).mockResolvedValue(respuesta)
    vi.mocked(ingestaApi.enviarArchivo).mockResolvedValue(respuesta)
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

    expect(ingestaApi.enviarTexto).toHaveBeenCalledWith(TEXTO_VALIDO)
    expect(analisisApi.iniciar).toHaveBeenCalledWith('texto normalizado')
    expect(await screen.findByText('Pantalla de resultados')).toBeInTheDocument()
  })

  it('exige una dirección en la pestaña de URL', async () => {
    renderIngesta()
    await userEvent.click(screen.getByRole('tab', { name: 'Desde URL' }))

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(screen.getByText('Por favor ingresa una URL válida.')).toBeInTheDocument()
    expect(ningunaViaLlamada()).toBe(true)
  })

  it('muestra el detalle de error que devuelve el servidor', async () => {
    vi.mocked(ingestaApi.enviarTexto).mockRejectedValue({
      response: { data: { detail: 'El texto es demasiado corto para analizarlo.' } },
    })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(await screen.findByText('El texto es demasiado corto para analizarlo.')).toBeInTheDocument()
    expect(analisisApi.iniciar).not.toHaveBeenCalled()
  })

  it('explica el límite de intentos ante un 429', async () => {
    vi.mocked(ingestaApi.enviarTexto).mockRejectedValue({ response: { status: 429, data: { error: 'Rate limit exceeded' } } })
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
    expect(ningunaViaLlamada()).toBe(true)
  })

  it('no falla si el servidor devuelve la lista de errores de validación', async () => {
    vi.mocked(ingestaApi.enviarTexto).mockRejectedValue({
      response: { status: 422, data: { detail: [{ loc: ['body', 'texto'], msg: 'error' }] } },
    })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

    expect(await screen.findByText('Ocurrió un error. Intenta de nuevo.')).toBeInTheDocument()
  })

  describe('carga de archivo', () => {
    async function abrirPestanaArchivo() {
      renderIngesta()
      await userEvent.click(screen.getByRole('tab', { name: 'Desde archivo' }))
    }

    function seleccionar(archivo: File) {
      fireEvent.change(screen.getByLabelText(/Archivo de la política/), { target: { files: [archivo] } })
    }

    it('envía el archivo como FormData y continúa con el análisis', async () => {
      await abrirPestanaArchivo()
      const archivo = new File(['%PDF-1.4 contenido'], 'politica.pdf', { type: 'application/pdf' })
      seleccionar(archivo)
      expect(screen.getByText(/politica\.pdf/)).toBeInTheDocument()

      await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

      expect(ingestaApi.enviarArchivo).toHaveBeenCalledWith(archivo)
      expect(analisisApi.iniciar).toHaveBeenCalledWith('texto normalizado')
      expect(await screen.findByText('Pantalla de resultados')).toBeInTheDocument()
    })

    it('exige seleccionar un archivo', async () => {
      await abrirPestanaArchivo()
      await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

      expect(screen.getByText('Selecciona un archivo PDF o TXT.')).toBeInTheDocument()
      expect(ningunaViaLlamada()).toBe(true)
    })

    it('rechaza extensiones no permitidas sin enviarlas', async () => {
      await abrirPestanaArchivo()
      seleccionar(new File(['x'], 'politica.docx', { type: 'application/octet-stream' }))
      await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

      expect(screen.getByText('Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt).')).toBeInTheDocument()
      expect(ningunaViaLlamada()).toBe(true)
    })

    it('rechaza archivos de más de 5 MB sin enviarlos', async () => {
      await abrirPestanaArchivo()
      seleccionar(new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'grande.txt', { type: 'text/plain' }))
      await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

      expect(screen.getByText('El archivo supera el tamaño máximo de 5 MB.')).toBeInTheDocument()
      expect(ningunaViaLlamada()).toBe(true)
    })

    it('muestra el error del servidor para un PDF sin texto', async () => {
      const detalle = 'No se encontró texto en el PDF. Si es un documento escaneado, el sistema no puede leerlo.'
      vi.mocked(ingestaApi.enviarArchivo).mockRejectedValue({ response: { status: 422, data: { detail: detalle } } })
      await abrirPestanaArchivo()
      seleccionar(new File(['%PDF-1.4'], 'escaneado.pdf', { type: 'application/pdf' }))
      await userEvent.click(screen.getByRole('button', { name: 'Analizar política' }))

      expect(await screen.findByText(detalle)).toBeInTheDocument()
      expect(analisisApi.iniciar).not.toHaveBeenCalled()
    })
  })
})
