import axios from 'axios';

// Базовый URL API - жестко прописываем для production
const API_BASE_URL = '/api/v1';

// Создание экземпляра axios с базовыми настройками
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Включаем отправку cookies
});

// Интерцептор для добавления CSRF токена к запросам
apiClient.interceptors.request.use(
  (config) => {
    // Добавляем CSRF токен из localStorage к заголовкам
    const csrfToken = localStorage.getItem('csrf_token');
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Если получили ошибку CSRF токена, очищаем его из localStorage
    if (error.response?.status === 403 && 
        (error.response?.data?.error === 'Missing CSRF token' || 
         error.response?.data?.error === 'Invalid CSRF token')) {
      localStorage.removeItem('csrf_token');
    }
    // Убираем автоматическое перенаправление - пусть компоненты сами решают что делать
    return Promise.reject(error);
  }
);

// Типы экспортируются из '../types/api'
export type { ApiResponse, PaginatedResponse } from '../types/api'; 