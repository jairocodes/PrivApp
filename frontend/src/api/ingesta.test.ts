import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import apiClient from './client'
import { ingestaApi } from './ingesta'

describe('ingestaApi', () => {
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

  it('envía el archivo como FormData, sin convertirlo a JSON', async () => {
    const archivo = new File(['%PDF-1.4'], 'politica.pdf', { type: 'application/pdf' })

    await ingestaApi.enviarArchivo(archivo)

    const config = adaptador.mock.calls[0][0]
    expect(config.url).toBe('/api/ingesta/archivo')
    expect(config.data).toBeInstanceOf(FormData)
    expect((config.data as FormData).get('archivo')).toBe(archivo)
    // El navegador fija multipart/form-data con su separador.
    expect(String(config.headers['Content-Type'] ?? '')).not.toContain('application/json')
  })

  it('envía el texto y la URL como JSON', async () => {
    await ingestaApi.enviarTexto('texto de la política')
    await ingestaApi.enviarURL('https://ejemplo.com/privacidad')

    expect(JSON.parse(adaptador.mock.calls[0][0].data)).toEqual({ texto: 'texto de la política' })
    expect(JSON.parse(adaptador.mock.calls[1][0].data)).toEqual({ url: 'https://ejemplo.com/privacidad' })
  })
})
