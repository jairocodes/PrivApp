import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { adminApi } from '@/api/admin'
import type { ListadoUsuariosResponse, UsuarioAdmin } from '@/types/admin'
import AdminUsuarios from './AdminUsuarios'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))
vi.mock('@/api/admin', () => ({
  adminApi: { listarUsuarios: vi.fn(), cambiarEstadoUsuario: vi.fn() },
}))

const LUIS: UsuarioAdmin = {
  id: 3,
  nombre: 'Luis Pérez',
  email: 'luis@privapp.test',
  role: 'usuario',
  is_active: true,
  created_at: '2026-09-01T15:30:00Z',
}

function responderListado(parcial: Partial<ListadoUsuariosResponse>) {
  vi.mocked(adminApi.listarUsuarios).mockResolvedValue({
    data: { items: [], total: 0, page: 1, page_size: 10, ...parcial },
  } as Awaited<ReturnType<typeof adminApi.listarUsuarios>>)
}

function renderPantalla() {
  render(
    <MemoryRouter>
      <AdminUsuarios />
    </MemoryRouter>,
  )
}

describe('AdminUsuarios', () => {
  it('lista las cuentas con su rol y estado', async () => {
    responderListado({
      items: [LUIS, { ...LUIS, id: 4, nombre: 'Eva', email: 'eva@privapp.test', is_active: false }],
      total: 2,
    })
    renderPantalla()

    expect(await screen.findByText('Luis Pérez')).toBeInTheDocument()
    expect(screen.getByText('luis@privapp.test')).toBeInTheDocument()
    expect(screen.getByText('Activa')).toBeInTheDocument()
    expect(screen.getByText('Desactivada')).toBeInTheDocument()
    expect(adminApi.listarUsuarios).toHaveBeenCalledWith(1, 10, '')
  })

  it('busca por nombre o correo', async () => {
    responderListado({ items: [LUIS], total: 1 })
    renderPantalla()
    await screen.findByText('Luis Pérez')

    await userEvent.type(screen.getByRole('searchbox', { name: 'Buscar por nombre o correo' }), '  luis ')
    await userEvent.click(screen.getByRole('button', { name: 'Buscar' }))

    expect(adminApi.listarUsuarios).toHaveBeenLastCalledWith(1, 10, 'luis')
  })

  it('informa cuando la búsqueda no encuentra usuarios', async () => {
    responderListado({})
    renderPantalla()

    expect(await screen.findByText('No se encontraron usuarios.')).toBeInTheDocument()
  })

  it('muestra un error si no se puede cargar el listado', async () => {
    vi.mocked(adminApi.listarUsuarios).mockRejectedValue(new Error('403'))
    renderPantalla()

    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar el listado de usuarios.')
  })

  it('pagina conservando la búsqueda', async () => {
    responderListado({ items: [LUIS], total: 15 })
    renderPantalla()
    await screen.findByText('Página 1 de 2')

    await userEvent.type(screen.getByRole('searchbox', { name: 'Buscar por nombre o correo' }), 'pérez')
    await userEvent.click(screen.getByRole('button', { name: 'Buscar' }))
    await screen.findByText('Página 1 de 2')
    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(adminApi.listarUsuarios).toHaveBeenLastCalledWith(2, 10, 'pérez')
  })
})
