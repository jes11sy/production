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

// Флаг для предотвращения множественных попыток обновления токена
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: any) => void;
  reject: (error: any) => void;
}> = [];

// Функция для очередности запросов во время обновления токена
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};

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
  async (error) => {
    const originalRequest = error.config;

    // Обработка 401 ошибок (Unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Если уже идет процесс обновления токена, добавляем запрос в очередь
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          return apiClient(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Пытаемся обновить CSRF токен через повторный запрос /me
        const response = await apiClient.get('/auth/me');
        const newCsrfToken = response.headers['x-csrf-token'] || response.data.csrf_token;
        
        if (newCsrfToken) {
          localStorage.setItem('csrf_token', newCsrfToken);
          processQueue(null, newCsrfToken);
          
          // Повторяем оригинальный запрос с новым токеном
          originalRequest.headers['X-CSRF-Token'] = newCsrfToken;
          return apiClient(originalRequest);
        } else {
          throw new Error('No CSRF token received');
        }
      } catch (refreshError) {
        // Если не удалось обновить токен, очищаем локальные данные
        localStorage.removeItem('csrf_token');
        processQueue(refreshError, null);
        
        // Уведомляем приложение о необходимости повторной авторизации
        window.dispatchEvent(new CustomEvent('auth-error', { detail: refreshError }));
        
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    // Обработка ошибок CSRF токена
    if (error.response?.status === 403 && 
        (error.response?.data?.error === 'Missing CSRF token' || 
         error.response?.data?.error === 'Invalid CSRF token')) {
      localStorage.removeItem('csrf_token');
      
      // Пытаемся получить новый CSRF токен
      try {
        const response = await apiClient.get('/auth/me');
        const newCsrfToken = response.headers['x-csrf-token'] || response.data.csrf_token;
        
        if (newCsrfToken) {
          localStorage.setItem('csrf_token', newCsrfToken);
          // Повторяем оригинальный запрос
          originalRequest.headers['X-CSRF-Token'] = newCsrfToken;
          return apiClient(originalRequest);
        }
      } catch (csrfError) {
        console.error('Failed to refresh CSRF token:', csrfError);
      }
    }

    // Для всех остальных ошибок - возвращаем как есть
    return Promise.reject(error);
  }
);

// Типы экспортируются из '../types/api'
export type { ApiResponse, PaginatedResponse } from '../types/api'; 