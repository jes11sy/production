import { apiClient } from './client';
import type { 
  Request, 
  CreateRequestData,
  UpdateRequestData,
  RequestType, 
  Direction, 
  Master
} from '../types/api';

// Реэкспорт основных типов для удобства
export type { Request, RequestType, Direction, Master } from '../types/api';

// Локальные CRUD типы для совместимости
export type CreateRequest = CreateRequestData;
export type UpdateRequest = UpdateRequestData;

// API методы для заявок
export const requestsApi = {
  // Получение списка заявок
  getRequests: async (params?: {
    page?: number;
    size?: number;
    status?: string;
    city_id?: number;
    master_id?: number;
  }): Promise<Request[]> => {
    const response = await apiClient.get('/requests/', { params });
    return response.data;
  },

  // Получение заявки по ID
  getRequest: async (id: number): Promise<Request> => {
    const response = await apiClient.get(`/requests/${id}/`);
    return response.data;
  },

  // Создание новой заявки
  createRequest: async (data: CreateRequest): Promise<Request> => {
    const response = await apiClient.post('/requests/', data);
    return response.data;
  },

  // Обновление заявки
  updateRequest: async (id: number, data: UpdateRequest): Promise<Request> => {
    const response = await apiClient.put(`/requests/${id}/`, data);
    return response.data;
  },

  // Удаление заявки
  deleteRequest: async (id: number): Promise<void> => {
    await apiClient.delete(`/requests/${id}/`);
  },

  // Получение типов заявок
  getRequestTypes: async (): Promise<RequestType[]> => {
    const response = await apiClient.get('/requests/request-types/');
    return response.data;
  },

  // Получение направлений
  getDirections: async (): Promise<Direction[]> => {
    const response = await apiClient.get('/requests/directions/');
    return response.data;
  },

  // Получение списка мастеров
  getMasters: async (): Promise<Master[]> => {
    try {
      const response = await apiClient.get('/requests/masters/');
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error('Ошибка загрузки мастеров:', error);
      return [];
    }
  },

  // Загрузка БСО к заявке
  uploadBso: async (requestId: number, file: File): Promise<{ file_path: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/requests/${requestId}/upload-bso/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Загрузка чека расхода к заявке
  uploadExpense: async (requestId: number, file: File): Promise<{ file_path: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/requests/${requestId}/upload-expense/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Загрузка аудиозаписи к заявке
  uploadRecording: async (requestId: number, file: File): Promise<{ file_path: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/requests/${requestId}/upload-recording/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
}; 