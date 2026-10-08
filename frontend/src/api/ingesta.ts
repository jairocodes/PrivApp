import apiClient from './client'
import type { IngestaResponse } from '@/types/ingesta'

export const ingestaApi = {
  enviarTexto: (texto: string) =>
    apiClient.post<IngestaResponse>('/api/ingesta/texto', { texto }),

  enviarURL: (url: string) =>
    apiClient.post<IngestaResponse>('/api/ingesta/url', { url }),

  enviarArchivo: (archivo: File) => {
    const formulario = new FormData()
    formulario.append('archivo', archivo)
    // Sin esta cabecera axios convertiría el FormData a JSON (el cliente usa
    // application/json por defecto); el navegador completa el separador.
    return apiClient.post<IngestaResponse>('/api/ingesta/archivo', formulario, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
