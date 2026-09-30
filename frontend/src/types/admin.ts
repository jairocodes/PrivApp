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
