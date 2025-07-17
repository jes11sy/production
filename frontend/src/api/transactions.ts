import { apiClient } from './client';
import type { 
  Transaction, 
  CreateTransactionData,
  UpdateTransactionData,
  TransactionType
} from '../types/api';

// Локальные CRUD типы для совместимости
export type TransactionCreate = CreateTransactionData;
export type TransactionUpdate = UpdateTransactionData;

export const transactionsApi = {
  // Получение списка транзакций
  getTransactions: async (): Promise<Transaction[]> => {
    const response = await apiClient.get('/transactions/');
    return response.data;
  },

  // Получение транзакции по ID
  getTransaction: async (id: number): Promise<Transaction> => {
    const response = await apiClient.get(`/transactions/${id}`);
    return response.data;
  },

  // Создание транзакции
  createTransaction: async (transaction: TransactionCreate): Promise<Transaction> => {
    const response = await apiClient.post('/transactions/', transaction);
    return response.data;
  },

  // Обновление транзакции
  updateTransaction: async (id: number, transaction: TransactionUpdate): Promise<Transaction> => {
    const response = await apiClient.put(`/transactions/${id}`, transaction);
    return response.data;
  },

  // Удаление транзакции
  deleteTransaction: async (id: number): Promise<void> => {
    await apiClient.delete(`/transactions/${id}`);
  },

  // Получение типов транзакций
  getTransactionTypes: async (): Promise<TransactionType[]> => {
    const response = await apiClient.get('/transactions/transaction-types/');
    return response.data;
  },

  // Получение городов
  getCities: async (): Promise<Array<{ id: number; name: string }>> => {
    const response = await apiClient.get('/transactions/cities/');
    return response.data;
  },

  // Загрузка файла для транзакции
  uploadFile: async (transactionId: number, file: File): Promise<{ file_path: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/transactions/${transactionId}/upload-file/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
}; 