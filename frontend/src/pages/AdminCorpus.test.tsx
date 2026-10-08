import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { adminApi } from '@/api/admin'
import type { DocumentoCorpus } from '@/types/admin'
import AdminCorpus from './AdminCorpus'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))
vi.mock('@/api/admin', () => ({
  adminApi: { listarCorpus: vi.fn(), cambiarEstadoDocumento: vi.fn(), cargarDocumento: vi.fn() },
}))

const RGPD: DocumentoCorpus = {
  documento_fuente: 'RGPD.pdf',
  jurisdiccion: 'internacional',
  fragmentos: 155,
  fecha_carga: '2026-05-18T12:00:00Z',
  activo: true,
}
const DECRETO: DocumentoCorpus = {
  documento_fuente: 'Decreto 57-2008.pdf',
  jurisdiccion: 'guatemala',
  fragmentos: 25,
  fecha_carga: '2026-05-18T12:00:00Z',
  activo: false,
}

function responderListado(documentos: DocumentoCorpus[]) {
  vi.mocked(adminApi.listarCorpus).mockResolvedValue({
    data: { documentos },
  } as Awaited<ReturnType<typeof adminApi.listarCorpus>>)
}

function renderPantalla() {
  render(
    <MemoryRouter>
      <AdminCorpus />
    </MemoryRouter>,
  )
}

describe('AdminCorpus', () => {
  beforeEach(() => {
    responderListado([RGPD, DECRETO])
  })

  it('lista los documentos con jurisdicción, fragmentos y estado', async () => {
    renderPantalla()

    expect(await screen.findByText('RGPD.pdf')).toBeInTheDocument()
    expect(screen.getByText(/Internacional · 155 fragmentos/)).toBeInTheDocument()
    expect(screen.getByText(/Guatemala · 25 fragmentos/)).toBeInTheDocument()
    expect(screen.getByText('Activo')).toBeInTheDocument()
    expect(screen.getByText('Desactivado')).toBeInTheDocument()
  })

  it('informa cuando el corpus está vacío', async () => {
    responderListado([])
    renderPantalla()
    expect(await screen.findByText('El corpus no tiene documentos cargados.')).toBeInTheDocument()
  })

  it('muestra un error si no se puede cargar el corpus', async () => {
    vi.mocked(adminApi.listarCorpus).mockRejectedValue(new Error('403'))
    renderPantalla()
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar el corpus normativo.')
  })

  it('desactiva un documento tras confirmar', async () => {
    vi.mocked(adminApi.cambiarEstadoDocumento).mockResolvedValue({
      data: { ...RGPD, activo: false },
    } as Awaited<ReturnType<typeof adminApi.cambiarEstadoDocumento>>)
    renderPantalla()

    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar RGPD.pdf' }))
    const dialogo = screen.getByRole('alertdialog', { name: '¿Desactivar «RGPD.pdf»?' })
    expect(dialogo).toHaveTextContent('dejarán de considerarse en los análisis nuevos')
    expect(adminApi.cambiarEstadoDocumento).not.toHaveBeenCalled()

    await userEvent.click(within(dialogo).getByRole('button', { name: 'Desactivar' }))

    expect(adminApi.cambiarEstadoDocumento).toHaveBeenCalledWith('RGPD.pdf', false)
    expect(await screen.findByRole('button', { name: 'Activar RGPD.pdf' })).toBeInTheDocument()
  })

  it('activa un documento desactivado', async () => {
    vi.mocked(adminApi.cambiarEstadoDocumento).mockResolvedValue({
      data: { ...DECRETO, activo: true },
    } as Awaited<ReturnType<typeof adminApi.cambiarEstadoDocumento>>)
    renderPantalla()

    await userEvent.click(await screen.findByRole('button', { name: 'Activar Decreto 57-2008.pdf' }))
    await userEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Activar' }))

    expect(adminApi.cambiarEstadoDocumento).toHaveBeenCalledWith('Decreto 57-2008.pdf', true)
    expect(await screen.findByRole('button', { name: 'Desactivar Decreto 57-2008.pdf' })).toBeInTheDocument()
  })

  it('agrega a la lista el documento recién cargado', async () => {
    vi.mocked(adminApi.cargarDocumento).mockResolvedValue({
      data: { ...RGPD, documento_fuente: 'Acuerdo nuevo.pdf', fragmentos: 12, fragmentos_insertados: 12, fragmentos_duplicados: 0 },
    } as Awaited<ReturnType<typeof adminApi.cargarDocumento>>)
    renderPantalla()
    await screen.findByText('RGPD.pdf')

    fireEvent.change(screen.getByLabelText(/Archivo \(PDF o TXT/), {
      target: { files: [new File(['%PDF-1.4'], 'Acuerdo nuevo.pdf', { type: 'application/pdf' })] },
    })
    await userEvent.selectOptions(screen.getByLabelText('Jurisdicción'), 'internacional')
    await userEvent.click(screen.getByRole('button', { name: 'Cargar documento' }))

    const nombres = (await screen.findAllByRole('listitem')).map((li) => li.querySelector('p')?.textContent)
    expect(nombres).toEqual(['Acuerdo nuevo.pdf', 'Decreto 57-2008.pdf', 'RGPD.pdf'])
  })

  it('cancelar no cambia el estado', async () => {
    renderPantalla()

    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar RGPD.pdf' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(adminApi.cambiarEstadoDocumento).not.toHaveBeenCalled()
  })
})
