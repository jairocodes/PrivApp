/** Si el texto parece una política de privacidad (RN-18). */
export interface DeteccionPolitica {
  resultado: 'politica' | 'dudosa' | 'no_politica'
  temas_encontrados: string[]
  temas_total: number
  cobertura: number
  voz_responsable: number
}

export interface IngestaResponse {
  texto_procesado: string
  caracteres: number
  palabras: number
  fuente: string
  deteccion?: DeteccionPolitica
}
