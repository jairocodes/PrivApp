import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { adminApi } from '@/api/admin'
import { AuthContext } from '@/context/AuthContext'
import { administrador, crearAuthValue } from '@/test/fixtures'
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
    <AuthContext.Provider value={crearAuthValue({ user: administrador, token: 't' })}>
      <MemoryRouter>
        <AdminUsuarios />
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

const ADMIN_EN_LISTA: UsuarioAdmin = {
  ...LUIS,
  id: administrador.id,
  nombre: administrador.nombre,
  email: administrador.email,
  role: 'administrador',
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

  it('desactiva una cuenta tras confirmar', async () => {
    responderListado({ items: [LUIS], total: 1 })
    vi.mocked(adminApi.cambiarEstadoUsuario).mockResolvedValue({
      data: { ...LUIS, is_active: false },
    } as Awaited<ReturnType<typeof adminApi.cambiarEstadoUsuario>>)
    renderPantalla()

    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar la cuenta de Luis Pérez' }))
    const dialogo = screen.getByRole('alertdialog', { name: '¿Desactivar la cuenta de Luis Pérez?' })
    expect(dialogo).toHaveTextContent('se cerrarán todas sus sesiones activas')
    expect(adminApi.cambiarEstadoUsuario).not.toHaveBeenCalled()

    await userEvent.click(within(dialogo).getByRole('button', { name: 'Desactivar' }))

    expect(adminApi.cambiarEstadoUsuario).toHaveBeenCalledWith(3, false)
    expect(await screen.findByText('Desactivada')).toBeInTheDocument()
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Activar la cuenta de Luis Pérez' })).toBeInTheDocument()
  })

  it('cancelar no cambia el estado', async () => {
    responderListado({ items: [LUIS], total: 1 })
    renderPantalla()

    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar la cuenta de Luis Pérez' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(adminApi.cambiarEstadoUsuario).not.toHaveBeenCalled()
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(screen.getByText('Activa')).toBeInTheDocument()
  })

  it('activa una cuenta desactivada', async () => {
    responderListado({ items: [{ ...LUIS, is_active: false }], total: 1 })
    vi.mocked(adminApi.cambiarEstadoUsuario).mockResolvedValue({
      data: LUIS,
    } as Awaited<ReturnType<typeof adminApi.cambiarEstadoUsuario>>)
    renderPantalla()

    await userEvent.click(await screen.findByRole('button', { name: 'Activar la cuenta de Luis Pérez' }))
    await userEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Activar' }))

    expect(adminApi.cambiarEstadoUsuario).toHaveBeenCalledWith(3, true)
    expect(await screen.findByText('Activa')).toBeInTheDocument()
  })

  it('muestra el error del servidor dentro del diálogo', async () => {
    responderListado({ items: [LUIS], total: 1 })
    vi.mocked(adminApi.cambiarEstadoUsuario).mockRejectedValue({
      response: { data: { detail: 'Usuario no encontrado.' } },
    })
    renderPantalla()

    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar la cuenta de Luis Pérez' }))
    await userEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Desactivar' }))

    expect(await screen.findByText('Usuario no encontrado.')).toBeInTheDocument()
    expect(screen.getByRole('alertdialog')).toBeInTheDocument()
  })

  it('no ofrece desactivar la cuenta propia', async () => {
    responderListado({ items: [ADMIN_EN_LISTA, LUIS], total: 2 })
    renderPantalla()

    expect(await screen.findByText('Tu cuenta')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: `Desactivar la cuenta de ${administrador.nombre}` })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Desactivar la cuenta de Luis Pérez' })).toBeInTheDocument()
  })
})
