import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { analisisApi, limiteDelDia, parametrosDeFiltros } from './analisis'
import apiClient from './client'

describe('limiteDelDia', () => {
  it('convierte el día local en el inicio y el final de ese día', () => {
    expect(limiteDelDia('2026-09-10', 'inicio')).toBe(new Date(2026, 8, 10, 0, 0, 0, 0).toISOString())
    expect(limiteDelDia('2026-09-10', 'fin')).toBe(new Date(2026, 8, 10, 23, 59, 59, 999).toISOString())
  })
})

describe('parametrosDeFiltros', () => {
  it('omite los filtros vacíos', () => {
    expect(parametrosDeFiltros({ texto: '   ', nivel: '', desde: '', hasta: '' })).toEqual({})
    expect(parametrosDeFiltros()).toEqual({})
  })

  it('traduce los filtros a los parámetros del servidor', () => {
    expect(parametrosDeFiltros({ texto: ' tiktok ', nivel: 'alto', desde: '2026-09-01', hasta: '2026-09-30' })).toEqual({
      q: 'tiktok',
      nivel: 'alto',
      desde: limiteDelDia('2026-09-01', 'inicio'),
      hasta: limiteDelDia('2026-09-30', 'fin'),
    })
  })
})

describe('analisisApi.listar', () => {
  const adaptadorOriginal = apiClient.defaults.adapter
  const adaptador = vi.fn(async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => ({
    data: {}, status: 200, statusText: '', headers: {}, config,
  }))

  beforeEach(() => {
    apiClient.defaults.adapter = adaptador
  })

  afterEach(() => {
    apiClient.defaults.adapter = adaptadorOriginal
  })

  it('envía la página y los filtros como parámetros', async () => {
    await analisisApi.listar(2, 10, { nivel: 'medio', texto: 'spotify' })

    expect(adaptador.mock.calls[0][0].params).toEqual({ page: 2, page_size: 10, nivel: 'medio', q: 'spotify' })
  })
})
