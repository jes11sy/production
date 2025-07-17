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

// Интерцептор для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Убираем автоматическое перенаправление - пусть компоненты сами решают что делать
    return Promise.reject(error);
  }
);

// Типы экспортируются из '../types/api'
export type { ApiResponse, PaginatedResponse } from '../types/api'; 