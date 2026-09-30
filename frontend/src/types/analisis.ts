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
  // Ausente en los análisis realizados antes de incorporar la clasificación.
  tipo_tratamiento?: string | null
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

export interface AnalisisHistorialItem {
  id_analisis: string
  fecha: string
  nivel_riesgo_global: NivelRiesgo
  puntaje: number
  comentario_breve: string
}

export interface HistorialResponse {
  items: AnalisisHistorialItem[]
  total: number
  page: number
  page_size: number
}

export interface AnalisisIniciado {
  id_analisis: string
  estado: 'procesando'
}

export type EstadoAnalisis = 'procesando' | 'completado' | 'error'

export interface AnalisisEstado {
  estado: EstadoAnalisis
  seccion_actual: number
  secciones_total: number | null
}

/** Filtros del historial tal como los ingresa la persona (fechas AAAA-MM-DD locales). */
export interface FiltrosHistorial {
  texto?: string
  nivel?: NivelRiesgo | ''
  desde?: string
  hasta?: string
}
