import apiClient from './client'

export const ingestaApi = {
  enviarTexto: (texto: string) =>
    apiClient.post<{ texto_procesado: string; id_analisis: string }>(
      '/api/ingesta/texto',
      { texto },
    ),

  enviarURL: (url: string) =>
    apiClient.post<{ texto_procesado: string; id_analisis: string }>(
      '/api/ingesta/url',
      { url },
    ),
}
