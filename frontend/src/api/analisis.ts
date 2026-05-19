import apiClient from './client'
import type { AnalisisResult } from '@/types/analisis'

export const analisisApi = {
  // El endpoint devuelve el AnalisisResult completo directamente (status 201)
  iniciar: (texto: string) =>
    apiClient.post<AnalisisResult>('/api/analisis/iniciar', { texto }),

  obtener: (id: string | number) =>
    apiClient.get<AnalisisResult>(`/api/analisis/${id}`),
}
