import { fireEvent, render, screen, within } from '@testing-library/react'
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
const REVISAR = { name: 'Revisar texto' }
const CONFIRMAR = { name: 'Confirmar y analizar' }

const ningunaViaLlamada = () =>
  [ingestaApi.enviarTexto, ingestaApi.enviarURL, ingestaApi.enviarArchivo].every(
    (via) => vi.mocked(via).mock.calls.length === 0,
  )

function responder(fuente: string) {
  return {
    data: { texto_procesado: 'texto normalizado', caracteres: 400, palabras: 50, fuente },
  } as Awaited<ReturnType<typeof ingestaApi.enviarTexto>>
}

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

async function revisarTextoValido() {
  renderIngesta()
  escribirTexto(TEXTO_VALIDO)
  await userEvent.click(screen.getByRole('button', REVISAR))
  await screen.findByRole('heading', { name: 'Revisa el texto antes de analizarlo' })
}

describe('IngestaForm', () => {
  beforeEach(() => {
    vi.mocked(ingestaApi.enviarTexto).mockResolvedValue(responder('texto_directo'))
    vi.mocked(ingestaApi.enviarURL).mockResolvedValue(responder('https://ejemplo.com/privacidad'))
    vi.mocked(ingestaApi.enviarArchivo).mockResolvedValue(responder('politica.pdf'))
    vi.mocked(analisisApi.iniciar).mockResolvedValue({
      data: { id_analisis: '5', estado: 'procesando' },
    } as Awaited<ReturnType<typeof analisisApi.iniciar>>)
  })

  it('marca el paso actual del análisis', async () => {
    renderIngesta()
    const pasos = screen.getByRole('list', { name: 'Pasos del análisis' })
    expect(within(pasos).getByText('1 · Pega o sube').closest('li')).toHaveAttribute('aria-current', 'step')

    escribirTexto(TEXTO_VALIDO)
    await userEvent.click(screen.getByRole('button', REVISAR))
    await screen.findByRole('heading', { name: 'Revisa el texto antes de analizarlo' })

    const pasosVistaPrevia = screen.getByRole('list', { name: 'Pasos del análisis' })
    expect(within(pasosVistaPrevia).getByText('2 · Revisa el texto').closest('li')).toHaveAttribute('aria-current', 'step')
  })

  it('no permite enviar un texto por debajo del mínimo', () => {
    renderIngesta()
    escribirTexto('Texto demasiado corto')

    expect(screen.getByText('(mínimo 200)')).toBeInTheDocument()
    expect(screen.getByRole('button', REVISAR)).toBeDisabled()
  })

  describe('vista previa y confirmación', () => {
    it('muestra el texto normalizado y su número de caracteres sin iniciar el análisis', async () => {
      await revisarTextoValido()

      expect(ingestaApi.enviarTexto).toHaveBeenCalledWith(TEXTO_VALIDO)
      expect(screen.getByLabelText('Texto que se analizará')).toHaveTextContent('texto normalizado')
      expect(screen.getByText('400')).toBeInTheDocument()
      expect(analisisApi.iniciar).not.toHaveBeenCalled()
    })

    it('confirmar inicia el análisis con el texto normalizado y navega a los resultados', async () => {
      await revisarTextoValido()

      await userEvent.click(screen.getByRole('button', CONFIRMAR))

      expect(analisisApi.iniciar).toHaveBeenCalledWith('texto normalizado', false)
      expect(await screen.findByText('Pantalla de resultados')).toBeInTheDocument()
    })

    it('con un texto dudoso exige confirmar que es una política y lo envía confirmado', async () => {
      vi.mocked(ingestaApi.enviarTexto).mockResolvedValue({
        data: {
          ...responder('texto_directo').data,
          deteccion: {
            resultado: 'dudosa', temas_encontrados: ['privacidad'], temas_total: 10, cobertura: 0.7, voz_responsable: 0,
          },
        },
      } as Awaited<ReturnType<typeof ingestaApi.enviarTexto>>)
      await revisarTextoValido()

      const confirmar = screen.getByRole('button', CONFIRMAR)
      expect(confirmar).toBeDisabled()
      await userEvent.click(screen.getByRole('checkbox', { name: /Confirmo que este texto es una política/ }))
      await userEvent.click(confirmar)

      expect(analisisApi.iniciar).toHaveBeenCalledWith('texto normalizado', true)
    })

    it('cancelar no inicia el análisis y descarta lo ingresado', async () => {
      await revisarTextoValido()

      await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

      expect(analisisApi.iniciar).not.toHaveBeenCalled()
      expect(screen.getByPlaceholderText(/Pega aquí el texto completo/)).toHaveValue('')
    })

    it('corregir vuelve al formulario conservando el texto', async () => {
      await revisarTextoValido()

      await userEvent.click(screen.getByRole('button', { name: 'Corregir' }))

      expect(analisisApi.iniciar).not.toHaveBeenCalled()
      expect(screen.getByPlaceholderText(/Pega aquí el texto completo/)).toHaveValue(TEXTO_VALIDO)
    })

    it('muestra en la vista previa un error al iniciar el análisis', async () => {
      vi.mocked(analisisApi.iniciar).mockRejectedValue({ response: { status: 429 } })
      await revisarTextoValido()

      await userEvent.click(screen.getByRole('button', CONFIRMAR))

      expect(await screen.findByRole('alert')).toHaveTextContent('Hiciste demasiados intentos.')
      expect(screen.getByRole('button', CONFIRMAR)).toBeEnabled()
    })

    it('la dirección web también pasa por la vista previa', async () => {
      renderIngesta()
      await userEvent.click(screen.getByRole('tab', { name: 'Desde URL' }))
      await userEvent.type(screen.getByPlaceholderText(/ejemplo\.com/), ' https://ejemplo.com/privacidad ')
      await userEvent.click(screen.getByRole('button', REVISAR))

      expect(ingestaApi.enviarURL).toHaveBeenCalledWith('https://ejemplo.com/privacidad')
      expect(await screen.findByText('Dirección web: https://ejemplo.com/privacidad')).toBeInTheDocument()
      expect(analisisApi.iniciar).not.toHaveBeenCalled()

      await userEvent.click(screen.getByRole('button', CONFIRMAR))
      expect(analisisApi.iniciar).toHaveBeenCalledWith('texto normalizado', false)
    })
  })

  it('exige una dirección en la pestaña de URL', async () => {
    renderIngesta()
    await userEvent.click(screen.getByRole('tab', { name: 'Desde URL' }))

    await userEvent.click(screen.getByRole('button', REVISAR))

    expect(screen.getByText('Por favor ingresa una URL válida.')).toBeInTheDocument()
    expect(ningunaViaLlamada()).toBe(true)
  })

  it('muestra el detalle de error que devuelve el servidor', async () => {
    vi.mocked(ingestaApi.enviarTexto).mockRejectedValue({
      response: { data: { detail: 'El texto es demasiado corto para analizarlo.' } },
    })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', REVISAR))

    expect(await screen.findByText('El texto es demasiado corto para analizarlo.')).toBeInTheDocument()
    expect(analisisApi.iniciar).not.toHaveBeenCalled()
  })

  it('explica el límite de intentos ante un 429', async () => {
    vi.mocked(ingestaApi.enviarTexto).mockRejectedValue({ response: { status: 429, data: { error: 'Rate limit exceeded' } } })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', REVISAR))

    expect(await screen.findByText('Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.')).toBeInTheDocument()
  })

  it('exige 40 palabras aunque el texto supere los 200 caracteres', async () => {
    renderIngesta()
    escribirTexto('a'.repeat(250))

    await userEvent.click(screen.getByRole('button', REVISAR))

    expect(screen.getByText('El texto debe tener al menos 200 caracteres y 40 palabras.')).toBeInTheDocument()
    expect(ningunaViaLlamada()).toBe(true)
  })

  it('no falla si el servidor devuelve la lista de errores de validación', async () => {
    vi.mocked(ingestaApi.enviarTexto).mockRejectedValue({
      response: { status: 422, data: { detail: [{ loc: ['body', 'texto'], msg: 'error' }] } },
    })
    renderIngesta()
    escribirTexto(TEXTO_VALIDO)

    await userEvent.click(screen.getByRole('button', REVISAR))

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

    it('envía el archivo, muestra la vista previa y analiza al confirmar', async () => {
      await abrirPestanaArchivo()
      const archivo = new File(['%PDF-1.4 contenido'], 'politica.pdf', { type: 'application/pdf' })
      seleccionar(archivo)
      expect(screen.getByText(/politica\.pdf ·/)).toBeInTheDocument()

      await userEvent.click(screen.getByRole('button', REVISAR))

      expect(ingestaApi.enviarArchivo).toHaveBeenCalledWith(archivo)
      expect(await screen.findByText('Archivo: politica.pdf')).toBeInTheDocument()
      expect(analisisApi.iniciar).not.toHaveBeenCalled()

      await userEvent.click(screen.getByRole('button', CONFIRMAR))
      expect(analisisApi.iniciar).toHaveBeenCalledWith('texto normalizado', false)
      expect(await screen.findByText('Pantalla de resultados')).toBeInTheDocument()
    })

    it('cancelar descarta también el archivo seleccionado', async () => {
      await abrirPestanaArchivo()
      seleccionar(new File(['%PDF-1.4'], 'politica.pdf', { type: 'application/pdf' }))
      await userEvent.click(screen.getByRole('button', REVISAR))
      await userEvent.click(await screen.findByRole('button', { name: 'Cancelar' }))

      await userEvent.click(screen.getByRole('tab', { name: 'Desde archivo' }))
      expect(screen.queryByText(/politica\.pdf ·/)).not.toBeInTheDocument()
      expect(analisisApi.iniciar).not.toHaveBeenCalled()
    })

    it('exige seleccionar un archivo', async () => {
      await abrirPestanaArchivo()
      await userEvent.click(screen.getByRole('button', REVISAR))

      expect(screen.getByText('Selecciona un archivo PDF o TXT.')).toBeInTheDocument()
      expect(ningunaViaLlamada()).toBe(true)
    })

    it('rechaza extensiones no permitidas sin enviarlas', async () => {
      await abrirPestanaArchivo()
      seleccionar(new File(['x'], 'politica.docx', { type: 'application/octet-stream' }))
      await userEvent.click(screen.getByRole('button', REVISAR))

      expect(screen.getByText('Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt).')).toBeInTheDocument()
      expect(ningunaViaLlamada()).toBe(true)
    })

    it('rechaza archivos de más de 5 MB sin enviarlos', async () => {
      await abrirPestanaArchivo()
      seleccionar(new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'grande.txt', { type: 'text/plain' }))
      await userEvent.click(screen.getByRole('button', REVISAR))

      expect(screen.getByText('El archivo supera el tamaño máximo de 5 MB.')).toBeInTheDocument()
      expect(ningunaViaLlamada()).toBe(true)
    })

    it('muestra el error del servidor para un PDF sin texto', async () => {
      const detalle = 'No se encontró texto en el PDF. Si es un documento escaneado, el sistema no puede leerlo.'
      vi.mocked(ingestaApi.enviarArchivo).mockRejectedValue({ response: { status: 422, data: { detail: detalle } } })
      await abrirPestanaArchivo()
      seleccionar(new File(['%PDF-1.4'], 'escaneado.pdf', { type: 'application/pdf' }))
      await userEvent.click(screen.getByRole('button', REVISAR))

      expect(await screen.findByText(detalle)).toBeInTheDocument()
      expect(analisisApi.iniciar).not.toHaveBeenCalled()
    })
  })
})
