import axios, { type AxiosInstance, type AxiosResponse } from 'axios';
import type { 
  LoginForm, 
  LoginResponse, 
  User, 
  Request, 
  Transaction, 
  City, 
  RequestType, 
  Direction, 
  TransactionType,
  Master,
  Employee,
  Administrator,
  AdvertisingCampaign,
  RequestForm,
  TransactionForm,
  Role
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Включаем отправку cookies
    });

    // Response interceptor для обработки ошибок
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        // Убираем автоматическое перенаправление
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: LoginForm): Promise<LoginResponse> {
    const response: AxiosResponse<LoginResponse> = await this.api.post('/auth/login', credentials);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<User> = await this.api.get('/auth/me');
    return response.data;
  }

  // Requests endpoints
  async getRequests(skip = 0, limit = 100): Promise<Request[]> {
    const response: AxiosResponse<Request[]> = await this.api.get(`/requests/?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async getRequest(id: number): Promise<Request> {
    const response: AxiosResponse<Request> = await this.api.get(`/requests/${id}`);
    return response.data;
  }

  async createRequest(request: RequestForm): Promise<Request> {
    const response: AxiosResponse<Request> = await this.api.post('/requests/', request);
    return response.data;
  }

  async updateRequest(id: number, request: Partial<RequestForm>): Promise<Request> {
    const response: AxiosResponse<Request> = await this.api.put(`/requests/${id}`, request);
    return response.data;
  }

  async deleteRequest(id: number): Promise<void> {
    await this.api.delete(`/requests/${id}`);
  }

  // Transactions endpoints
  async getTransactions(skip = 0, limit = 100): Promise<Transaction[]> {
    const response: AxiosResponse<Transaction[]> = await this.api.get(`/transactions/?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async getTransaction(id: number): Promise<Transaction> {
    const response: AxiosResponse<Transaction> = await this.api.get(`/transactions/${id}`);
    return response.data;
  }

  async createTransaction(transaction: TransactionForm): Promise<Transaction> {
    const response: AxiosResponse<Transaction> = await this.api.post('/transactions/', transaction);
    return response.data;
  }

  async updateTransaction(id: number, transaction: Partial<TransactionForm>): Promise<Transaction> {
    const response: AxiosResponse<Transaction> = await this.api.put(`/transactions/${id}`, transaction);
    return response.data;
  }

  async deleteTransaction(id: number): Promise<void> {
    await this.api.delete(`/transactions/${id}`);
  }

  // Reference data endpoints
  async getCities(): Promise<City[]> {
    const response: AxiosResponse<City[]> = await this.api.get('/requests/cities/');
    return response.data;
  }

  async getRequestTypes(): Promise<RequestType[]> {
    const response: AxiosResponse<RequestType[]> = await this.api.get('/requests/request-types/');
    return response.data;
  }

  async getDirections(): Promise<Direction[]> {
    const response: AxiosResponse<Direction[]> = await this.api.get('/requests/directions/');
    return response.data;
  }

  async getTransactionTypes(): Promise<TransactionType[]> {
    const response: AxiosResponse<TransactionType[]> = await this.api.get('/transactions/transaction-types/');
    return response.data;
  }

  async getMasters(): Promise<Master[]> {
    const response: AxiosResponse<Master[]> = await this.api.get('/requests/masters/');
    return response.data;
  }

  async getAdvertisingCampaigns(): Promise<AdvertisingCampaign[]> {
    const response: AxiosResponse<AdvertisingCampaign[]> = await this.api.get('/requests/advertising-campaigns/');
    return response.data;
  }

  // Users endpoints
  async getEmployees(skip = 0, limit = 100): Promise<Employee[]> {
    const response: AxiosResponse<Employee[]> = await this.api.get(`/users/employees/?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async getAdministrators(skip = 0, limit = 100): Promise<Administrator[]> {
    const response: AxiosResponse<Administrator[]> = await this.api.get(`/users/administrators/?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async getRoles(): Promise<Role[]> {
    const response: AxiosResponse<Role[]> = await this.api.get('/users/roles/');
    return response.data;
  }
}

export const apiService = new ApiService(); 