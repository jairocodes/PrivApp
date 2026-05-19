export type NivelRiesgo = 'bajo' | 'medio' | 'alto'
export type TipoHallazgo = 'riesgo' | 'transparencia' | 'neutral'
export type Jurisdiccion = 'guatemala' | 'internacional' | 'estandar_tecnico'

export interface FuenteNormativa {
  documento: string
  referencia: string
  fragmento_relevante: string
}

export interface Hallazgo {
  tipo: TipoHallazgo
  descripcion: string
  nivel: NivelRiesgo
  fuentes_normativas: FuenteNormativa[]
}

export interface SeccionAnalizada {
  categoria_opp115: string
  titulo: string
  texto_original: string
  hallazgos: Hallazgo[]
}

export interface ResumenGeneral {
  nivel_riesgo_global: NivelRiesgo
  puntaje: number
  comentario_breve: string
}

export interface AnalisisResult {
  id_analisis: string
  fecha: string
  resumen_general: ResumenGeneral
  secciones_analizadas: SeccionAnalizada[]
  recomendaciones: string[]
}
