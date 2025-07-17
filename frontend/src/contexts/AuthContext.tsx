import React, { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../api/auth'
import type { User } from '../types/api'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (login: string, password: string) => Promise<User>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  const checkAuth = async () => {
    setIsLoading(true)
    try {
      const userData = await authApi.getCurrentUser()
      setUser(userData)
    } catch (error: unknown) {
      // Cookie недоступен или недействителен
      const status = (error as { response?: { status?: number } })?.response?.status;
      console.log('Auth check failed:', status)
      setUser(null)
      // Очищаем CSRF токен при ошибке аутентификации
      localStorage.removeItem('csrf_token')
    }
    setIsLoading(false)
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const login = async (login: string, password: string) => {
    const response = await authApi.login({ login, password })
    // Cookie устанавливается автоматически сервером
    
    // Сохраняем CSRF токен в localStorage
    if (response.csrf_token) {
      localStorage.setItem('csrf_token', response.csrf_token)
    }
    
    // Небольшая задержка для обработки cookie на сервере
    await new Promise(resolve => setTimeout(resolve, 100))
    
    try {
      // Получаем актуальные данные пользователя из /me
      const userData = await authApi.getCurrentUser()
      setUser(userData)
      return userData
    } catch {
      // Если не удалось получить данные из /me, создаем пользователя из ответа логина
      const userData: User = {
        id: response.user_id,
        login: login,
        status: 'active',
        user_type: response.user_type as 'admin' | 'employee' | 'master',
        role: response.role,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      
      setUser(userData)
      return userData
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
    // Очищаем CSRF токен при выходе
    localStorage.removeItem('csrf_token')
    setUser(null)
  }

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuth
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 