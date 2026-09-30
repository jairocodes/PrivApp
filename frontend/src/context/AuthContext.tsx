import { createContext, useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { authApi } from '@/api/auth'
import type { AuthContextValue, CambioPasswordRequest, User } from '@/types/auth'

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('access_token'),
  )
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (token) {
      authApi.me()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token')
          setToken(null)
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [token])

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login({ email, password })
    const { access_token } = res.data
    localStorage.setItem('access_token', access_token)
    setToken(access_token)
    const meRes = await authApi.me()
    setUser(meRes.data)
  }, [])

  const register = useCallback(
    async (nombre: string, email: string, password: string, aceptaAviso: boolean) => {
      const res = await authApi.register({ nombre, email, password, acepta_aviso: aceptaAviso })
      const { access_token } = res.data
      localStorage.setItem('access_token', access_token)
      setToken(access_token)
      const meRes = await authApi.me()
      setUser(meRes.data)
    },
    [],
  )

  const actualizarPerfil = useCallback(async (nombre: string) => {
    const res = await authApi.actualizarPerfil(nombre)
    setUser(res.data)
  }, [])

  // El servidor cierra todas las sesiones y devuelve un token nuevo para esta.
  const cambiarPassword = useCallback(async (datos: CambioPasswordRequest) => {
    const res = await authApi.cambiarPassword(datos)
    localStorage.setItem('access_token', res.data.access_token)
    setToken(res.data.access_token)
  }, [])

  // La cuenta ya no existe: basta con olvidar la sesión en este navegador.
  const eliminarCuenta = useCallback(async (password: string) => {
    await authApi.eliminarCuenta(password)
    localStorage.removeItem('access_token')
    setToken(null)
    setUser(null)
  }, [])

  const logout = useCallback(() => {
    authApi.logout().catch(() => {})
    localStorage.removeItem('access_token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, actualizarPerfil, cambiarPassword, eliminarCuenta }}>
      {children}
    </AuthContext.Provider>
  )
}
