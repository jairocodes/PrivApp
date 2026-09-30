export type Rol = 'usuario' | 'administrador'

export interface User {
  id: number
  nombre: string
  email: string
  role: Rol
}

export function esAdministrador(user: User | null): boolean {
  return user?.role === 'administrador'
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  nombre: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (nombre: string, email: string, password: string) => Promise<void>
  logout: () => void
}
