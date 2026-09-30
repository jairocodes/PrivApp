import apiClient from './client'
import type {
  DocumentoCargado,
  DocumentoCorpus,
  Jurisdiccion,
  ListadoUsuariosResponse,
  UsuarioAdmin,
} from '@/types/admin'

export const adminApi = {
  listarUsuarios: (page = 1, pageSize = 10, busqueda = '') =>
    apiClient.get<ListadoUsuariosResponse>('/api/admin/usuarios', {
      params: { page, page_size: pageSize, ...(busqueda ? { q: busqueda } : {}) },
    }),

  cambiarEstadoUsuario: (id: number, activo: boolean) =>
    apiClient.patch<UsuarioAdmin>(`/api/admin/usuarios/${id}/estado`, { activo }),

  listarCorpus: () =>
    apiClient.get<{ documentos: DocumentoCorpus[] }>('/api/admin/corpus'),

  cambiarEstadoDocumento: (documentoFuente: string, activo: boolean) =>
    apiClient.patch<DocumentoCorpus>('/api/admin/corpus/estado', {
      documento_fuente: documentoFuente,
      activo,
    }),

  cargarDocumento: (archivo: File, jurisdiccion: Jurisdiccion) => {
    const formulario = new FormData()
    formulario.append('archivo', archivo)
    formulario.append('jurisdiccion', jurisdiccion)
    // Sin esta cabecera axios convertiría el FormData a JSON.
    return apiClient.post<DocumentoCargado>('/api/admin/corpus', formulario, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
