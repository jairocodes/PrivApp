import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { adminApi } from '@/api/admin'
import type { DocumentoCargado } from '@/types/admin'
import FormCargaDocumento from './FormCargaDocumento'

vi.mock('@/api/admin', () => ({ adminApi: { cargarDocumento: vi.fn() } }))

const CARGADO: DocumentoCargado = {
  documento_fuente: 'Norma nueva.pdf',
  jurisdiccion: 'guatemala',
  fragmentos: 42,
  fecha_carga: '2026-09-30T12:00:00Z',
  activo: true,
  fragmentos_insertados: 42,
  fragmentos_duplicados: 0,
}

function renderForm() {
  const onCargado = vi.fn()
  render(<FormCargaDocumento onCargado={onCargado} />)
  return onCargado
}

function seleccionar(archivo: File) {
  fireEvent.change(screen.getByLabelText(/Archivo \(PDF o TXT/), { target: { files: [archivo] } })
}

const PDF = () => new File(['%PDF-1.4'], 'Norma nueva.pdf', { type: 'application/pdf' })

describe('FormCargaDocumento', () => {
  it('carga el documento con su jurisdicción y avisa del resultado', async () => {
    vi.mocked(adminApi.cargarDocumento).mockResolvedValue({
      data: CARGADO,
    } as Awaited<ReturnType<typeof adminApi.cargarDocumento>>)
    const onCargado = renderForm()
    const archivo = PDF()
    seleccionar(archivo)
    await userEvent.selectOptions(screen.getByLabelText('Jurisdicción'), 'guatemala')

    await userEvent.click(screen.getByRole('button', { name: 'Cargar documento' }))

    expect(adminApi.cargarDocumento).toHaveBeenCalledWith(archivo, 'guatemala')
    expect(onCargado).toHaveBeenCalledWith(CARGADO)
    expect(await screen.findByRole('status')).toHaveTextContent('Se incorporó «Norma nueva.pdf» con 42 fragmentos.')
    expect(screen.getByLabelText('Jurisdicción')).toHaveValue('')
  })

  it('exige un archivo', async () => {
    renderForm()
    await userEvent.selectOptions(screen.getByLabelText('Jurisdicción'), 'internacional')
    await userEvent.click(screen.getByRole('button', { name: 'Cargar documento' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Selecciona un archivo PDF o TXT.')
    expect(adminApi.cargarDocumento).not.toHaveBeenCalled()
  })

  it('exige la jurisdicción', async () => {
    renderForm()
    seleccionar(PDF())
    await userEvent.click(screen.getByRole('button', { name: 'Cargar documento' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Selecciona la jurisdicción del documento.')
    expect(adminApi.cargarDocumento).not.toHaveBeenCalled()
  })

  it('valida el tipo de archivo antes de enviarlo', async () => {
    renderForm()
    seleccionar(new File(['x'], 'norma.docx'))
    await userEvent.selectOptions(screen.getByLabelText('Jurisdicción'), 'guatemala')
    await userEvent.click(screen.getByRole('button', { name: 'Cargar documento' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt).')
    expect(adminApi.cargarDocumento).not.toHaveBeenCalled()
  })

  it('muestra el error del servidor, por ejemplo un nombre repetido', async () => {
    vi.mocked(adminApi.cargarDocumento).mockRejectedValue({
      response: { status: 409, data: { detail: 'Ya existe un documento con ese nombre en el corpus normativo.' } },
    })
    const onCargado = renderForm()
    seleccionar(PDF())
    await userEvent.selectOptions(screen.getByLabelText('Jurisdicción'), 'guatemala')
    await userEvent.click(screen.getByRole('button', { name: 'Cargar documento' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Ya existe un documento con ese nombre')
    expect(onCargado).not.toHaveBeenCalled()
  })
})
