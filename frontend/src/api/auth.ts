import { apiClient } from './client'
import type { AuthResponse, LoginCredentials, RegisterData, User } from '@/types'

export async function login(data: LoginCredentials): Promise<AuthResponse> {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)

  const response = await apiClient.post<AuthResponse>(
    '/auth/token',
    formData.toString(),
    {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    },
  )
  return response.data
}

export async function register(data: RegisterData): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data)
  return response.data
}

export async function refreshToken(): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/refresh')
  return response.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/revoke_token')
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>('/users/me')
  return response.data
}
