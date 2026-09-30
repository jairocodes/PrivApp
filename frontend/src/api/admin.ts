import apiClient from './client'
import type { ListadoUsuariosResponse, UsuarioAdmin } from '@/types/admin'

export const adminApi = {
  listarUsuarios: (page = 1, pageSize = 10, busqueda = '') =>
    apiClient.get<ListadoUsuariosResponse>('/api/admin/usuarios', {
      params: { page, page_size: pageSize, ...(busqueda ? { q: busqueda } : {}) },
    }),

  cambiarEstadoUsuario: (id: number, activo: boolean) =>
    apiClient.patch<UsuarioAdmin>(`/api/admin/usuarios/${id}/estado`, { activo }),
}
