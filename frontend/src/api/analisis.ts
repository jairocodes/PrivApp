import apiClient from './client'
import type { AnalisisEstado, AnalisisIniciado, AnalisisResult, HistorialResponse } from '@/types/analisis'

export const analisisApi = {
  // El análisis se procesa en segundo plano; este endpoint solo confirma que inició (202)
  iniciar: (texto: string) =>
    apiClient.post<AnalisisIniciado>('/api/analisis/iniciar', { texto }),

  consultarEstado: (id: string | number) =>
    apiClient.get<AnalisisEstado>(`/api/analisis/${id}/estado`),

  obtener: (id: string | number) =>
    apiClient.get<AnalisisResult>(`/api/analisis/${id}`),

  listar: (page = 1, pageSize = 10) =>
    apiClient.get<HistorialResponse>('/api/analisis', {
      params: { page, page_size: pageSize },
    }),

  descargarPDF: (id: string | number) =>
    apiClient.get<Blob>(`/api/analisis/${id}/pdf`, { responseType: 'blob' }),
}
