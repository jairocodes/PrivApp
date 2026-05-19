import apiClient from './client'
import type { AnalisisResult } from '@/types/analisis'

export const analisisApi = {
  iniciar: (texto: string) =>
    apiClient.post<{ id: number }>('/api/analisis/iniciar', { texto }),

  obtener: (id: string | number) =>
    apiClient.get<AnalisisResult>(`/api/analisis/${id}`),
}
