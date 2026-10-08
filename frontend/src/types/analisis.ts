export type NivelRiesgo = 'bajo' | 'medio' | 'alto'
export type TipoHallazgo = 'riesgo' | 'transparencia' | 'neutral'
export type Jurisdiccion = 'guatemala' | 'internacional' | 'estandar_tecnico'

export interface FuenteNormativa {
  documento: string
  referencia: string
  fragmento_relevante: string
  // La completa el servidor con el fragmento del corpus; ausente en análisis antiguos.
  jurisdiccion?: Jurisdiccion | null
}

export interface Hallazgo {
  tipo: TipoHallazgo
  descripcion: string
  nivel: NivelRiesgo
  fuentes_normativas: FuenteNormativa[]
  // Ausente en los análisis realizados antes de incorporar la clasificación.
  tipo_tratamiento?: string | null
  // Ningún fragmento del corpus respalda el hallazgo: no suma al puntaje.
  sin_respaldo?: boolean
  // Código del criterio de la rúbrica (A1–A10, M1–M5, B1–B4); ausente en análisis antiguos.
  criterio?: string | null
}

export interface SeccionAnalizada {
  categoria_opp115: string
  titulo: string
  texto_original: string
  hallazgos: Hallazgo[]
  // false si la sección no pudo analizarse: no cuenta para el nivel ni la puntuación.
  analizada?: boolean
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
  /** Por qué terminó con error, si se sabe (RN-18). */
  motivo?: 'no_es_politica' | null
}

/** Filtros del historial tal como los ingresa la persona (fechas AAAA-MM-DD locales). */
export interface FiltrosHistorial {
  texto?: string
  nivel?: NivelRiesgo | ''
  desde?: string
  hasta?: string
}

export interface DistribucionNiveles {
  bajo: number
  medio: number
  alto: number
}

export interface EstadisticasPersonales {
  total: number
  por_nivel: DistribucionNiveles
  puntaje_promedio: number
}
