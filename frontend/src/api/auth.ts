import { apiClient } from './client';
import type { User } from '../types/api';

// Локальные типы для аутентификации
export interface LoginRequest {
  login: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_type: string;
  role: string;
  user_id: number;
  city_id?: number;
  csrf_token: string;
}

// API методы для аутентификации
export const authApi = {
  // Вход в систему
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    return response.data;
  },

  // Получение информации о текущем пользователе
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  // Выход из системы
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
    // Cookie удаляется автоматически сервером
  },

  // Проверка валидности токена
  validateToken: async (): Promise<boolean> => {
    try {
      await apiClient.get('/auth/me');
      return true;
    } catch {
      return false;
    }
  }
}; 