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
export type CreateRequest = CreateRequestData;
export type UpdateRequest = UpdateRequestData;

export const requestsApi = {
  // Получение списка заявок
  getRequests: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    city_id?: number;
    master_id?: number;
    search?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<Request[]> => {
    // Добавляем timestamp для обхода кеша
    const paramsWithTimestamp = {
      ...params,
      _t: Date.now()
    };
    
    const response = await apiClient.get('/requests/', { 
      params: paramsWithTimestamp,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    return response.data;
  },

  // Получение заявки по ID
  getRequest: async (id: number): Promise<Request> => {
    const response = await apiClient.get(`/requests/${id}/`, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      params: {
        _t: Date.now() // Добавляем timestamp для гарантированного обхода кеша
      }
    });
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
    const response = await apiClient.get('/requests/request-types/', {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    return response.data;
  },

  // Получение направлений
  getDirections: async (): Promise<Direction[]> => {
    const response = await apiClient.get('/requests/directions/', {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    return response.data;
  },

  // Получение мастеров
  getMasters: async (): Promise<Master[]> => {
    const response = await apiClient.get('/requests/masters/', {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    return response.data;
  },

  // Загрузка файлов
  uploadBso: async (requestId: number, file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);
    await apiClient.post(`/requests/${requestId}/upload-bso/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  uploadExpense: async (requestId: number, file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);
    await apiClient.post(`/requests/${requestId}/upload-expense/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  uploadRecording: async (requestId: number, file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);
    await apiClient.post(`/requests/${requestId}/upload-recording/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
}; 