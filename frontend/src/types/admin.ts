import type { Rol } from './auth'

export interface UsuarioAdmin {
  id: number
  nombre: string
  email: string
  role: Rol
  is_active: boolean
  created_at: string
}

export interface ListadoUsuariosResponse {
  items: UsuarioAdmin[]
  total: number
  page: number
  page_size: number
}

export type Jurisdiccion = 'guatemala' | 'internacional' | 'estandar_tecnico'

export interface DocumentoCorpus {
  documento_fuente: string
  jurisdiccion: Jurisdiccion | string
  fragmentos: number
  fecha_carga: string | null
  activo: boolean
}

export interface DocumentoCargado extends DocumentoCorpus {
  fragmentos_insertados: number
  fragmentos_duplicados: number
}
