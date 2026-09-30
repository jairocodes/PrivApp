import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { authApi } from '@/api/auth'
import { useAuth } from '@/hooks/useAuth'
import { AuthProvider } from './AuthContext'

vi.mock('@/api/auth', () => ({
  authApi: { login: vi.fn(), register: vi.fn(), logout: vi.fn(), me: vi.fn(), actualizarPerfil: vi.fn() },
}))

const USUARIO = { id: 1, nombre: 'Ana', email: 'ana@privapp.test', role: 'usuario' }

const envoltorio = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.mocked(authApi.login).mockResolvedValue({ data: { access_token: 'token-nuevo', token_type: 'bearer' } } as never)
    vi.mocked(authApi.register).mockResolvedValue({ data: { access_token: 'token-registro', token_type: 'bearer' } } as never)
    vi.mocked(authApi.me).mockResolvedValue({ data: USUARIO } as never)
    vi.mocked(authApi.logout).mockResolvedValue({} as never)
  })

  it('sin token guardado termina de cargar sin usuario', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: envoltorio })

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.user).toBeNull()
    expect(authApi.me).not.toHaveBeenCalled()
  })

  it('recupera la sesión si hay un token guardado', async () => {
    localStorage.setItem('access_token', 'token-guardado')
    const { result } = renderHook(() => useAuth(), { wrapper: envoltorio })

    await waitFor(() => expect(result.current.user).toEqual(USUARIO))
    expect(result.current.token).toBe('token-guardado')
  })

  it('descarta un token guardado que el servidor rechaza', async () => {
    localStorage.setItem('access_token', 'token-vencido')
    vi.mocked(authApi.me).mockRejectedValue(new Error('401'))
    const { result } = renderHook(() => useAuth(), { wrapper: envoltorio })

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.token).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('login guarda el token y carga el usuario', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: envoltorio })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(() => result.current.login('ana@privapp.test', 'Segura123'))

    expect(authApi.login).toHaveBeenCalledWith({ email: 'ana@privapp.test', password: 'Segura123' })
    expect(localStorage.getItem('access_token')).toBe('token-nuevo')
    expect(result.current.user).toEqual(USUARIO)
  })

  it('register guarda el token y carga el usuario', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: envoltorio })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(() => result.current.register('Ana', 'ana@privapp.test', 'Segura123', true))

    expect(authApi.register).toHaveBeenCalledWith({
      nombre: 'Ana',
      email: 'ana@privapp.test',
      password: 'Segura123',
      acepta_aviso: true,
    })
    expect(localStorage.getItem('access_token')).toBe('token-registro')
    expect(result.current.user).toEqual(USUARIO)
  })

  it('logout revoca la sesión en el servidor y limpia el estado local', async () => {
    localStorage.setItem('access_token', 'token-guardado')
    const { result } = renderHook(() => useAuth(), { wrapper: envoltorio })
    await waitFor(() => expect(result.current.user).toEqual(USUARIO))

    act(() => result.current.logout())

    expect(authApi.logout).toHaveBeenCalled()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
  })

  it('actualizarPerfil guarda el usuario devuelto por el servidor', async () => {
    localStorage.setItem('access_token', 'token-guardado')
    vi.mocked(authApi.actualizarPerfil).mockResolvedValue({ data: { ...USUARIO, nombre: 'Ana María' } } as never)
    const { result } = renderHook(() => useAuth(), { wrapper: envoltorio })
    await waitFor(() => expect(result.current.user).toEqual(USUARIO))

    await act(() => result.current.actualizarPerfil('Ana María'))

    expect(authApi.actualizarPerfil).toHaveBeenCalledWith('Ana María')
    expect(result.current.user?.nombre).toBe('Ana María')
  })

  it('useAuth exige estar dentro del proveedor', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => renderHook(() => useAuth())).toThrow('useAuth debe usarse dentro de <AuthProvider>')
  })
})
