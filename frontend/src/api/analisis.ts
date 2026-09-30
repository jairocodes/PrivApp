import apiClient from './client'
import type {
  AnalisisEstado,
  AnalisisIniciado,
  AnalisisResult,
  FiltrosHistorial,
  HistorialResponse,
} from '@/types/analisis'

/** 'AAAA-MM-DD' en la hora local → instante ISO (UTC) del inicio o del final de ese día. */
export function limiteDelDia(fecha: string, extremo: 'inicio' | 'fin'): string {
  const [anio, mes, dia] = fecha.split('-').map(Number)
  const instante =
    extremo === 'inicio'
      ? new Date(anio, mes - 1, dia, 0, 0, 0, 0)
      : new Date(anio, mes - 1, dia, 23, 59, 59, 999)
  return instante.toISOString()
}

export function parametrosDeFiltros(filtros: FiltrosHistorial = {}): Record<string, string> {
  const parametros: Record<string, string> = {}
  const texto = filtros.texto?.trim()
  if (texto) parametros.q = texto
  if (filtros.nivel) parametros.nivel = filtros.nivel
  if (filtros.desde) parametros.desde = limiteDelDia(filtros.desde, 'inicio')
  if (filtros.hasta) parametros.hasta = limiteDelDia(filtros.hasta, 'fin')
  return parametros
}

export const analisisApi = {
  // El análisis se procesa en segundo plano; este endpoint solo confirma que inició (202)
  iniciar: (texto: string) =>
    apiClient.post<AnalisisIniciado>('/api/analisis/iniciar', { texto }),

  consultarEstado: (id: string | number) =>
    apiClient.get<AnalisisEstado>(`/api/analisis/${id}/estado`),

  obtener: (id: string | number) =>
    apiClient.get<AnalisisResult>(`/api/analisis/${id}`),

  listar: (page = 1, pageSize = 10, filtros: FiltrosHistorial = {}) =>
    apiClient.get<HistorialResponse>('/api/analisis', {
      params: { page, page_size: pageSize, ...parametrosDeFiltros(filtros) },
    }),

  // Eliminación definitiva; el servidor responde 204 sin contenido.
  eliminar: (id: string | number) =>
    apiClient.delete<void>(`/api/analisis/${id}`),

  descargarPDF: (id: string | number) =>
    apiClient.get<Blob>(`/api/analisis/${id}/pdf`, { responseType: 'blob' }),
}
