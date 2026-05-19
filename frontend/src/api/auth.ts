import apiClient from './client'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types/auth'

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>('/api/auth/login', data),

  register: (data: RegisterRequest) =>
    apiClient.post<TokenResponse>('/api/auth/register', data),

  logout: () =>
    apiClient.post('/api/auth/logout'),

  me: () =>
    apiClient.get<User>('/api/auth/me'),
}
