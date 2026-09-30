import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { AxiosHeaders } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import apiClient from './client'

function adaptadorQueResponde(status: number) {
  return vi.fn(async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
    const respuesta = { data: {}, status, statusText: '', headers: {}, config }
    if (status >= 400) {
      return Promise.reject(Object.assign(new Error(`HTTP ${status}`), { response: respuesta, config }))
    }
    return respuesta
  })
}

describe('apiClient', () => {
  const ubicacionOriginal = window.location

  afterEach(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: ubicacionOriginal })
  })

  it('agrega el token guardado como Authorization: Bearer', async () => {
    localStorage.setItem('access_token', 'mi-token')
    const adaptador = adaptadorQueResponde(200)

    await apiClient.get('/api/auth/me', { adapter: adaptador })

    const headers = AxiosHeaders.from(adaptador.mock.calls[0][0].headers)
    expect(headers.get('Authorization')).toBe('Bearer mi-token')
  })

  it('no envía Authorization sin token guardado', async () => {
    const adaptador = adaptadorQueResponde(200)

    await apiClient.get('/health', { adapter: adaptador })

    const headers = AxiosHeaders.from(adaptador.mock.calls[0][0].headers)
    expect(headers.has('Authorization')).toBe(false)
  })

  it('ante un 401 descarta el token y redirige al inicio de sesión', async () => {
    Object.defineProperty(window, 'location', { configurable: true, value: { href: '/historial' } })
    localStorage.setItem('access_token', 'token-vencido')

    await expect(
      apiClient.get('/api/analisis', { adapter: adaptadorQueResponde(401) }),
    ).rejects.toBeTruthy()

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(window.location.href).toBe('/login')
  })
})
