import { apiClient } from './client';
import type { 
  City, 
  Role, 
  Master, 
  Employee, 
  Administrator
} from '../types/api';

// Реэкспорт основных типов для удобства
export type { City, Role, Master, Employee, Administrator } from '../types/api';

// CRUD интерфейсы для мастеров
export interface MasterCreate {
  city_id: number;
  full_name: string;
  phone_number: string;
  birth_date?: string;
  passport?: string;
  status: string;
  chat_id?: string;
  login: string;
  password: string;
  notes?: string;
}

export type CreateMasterRequest = MasterCreate

export interface MasterUpdate extends Partial<MasterCreate> {
  password?: string;
}

// CRUD интерфейсы для сотрудников
export interface EmployeeCreate {
  name: string;
  role_id: number;
  status?: string;
  city_id?: number;
  login: string;
  password: string;
  notes?: string;
}

export interface EmployeeUpdate {
  name?: string;
  role_id?: number;
  status?: string;
  city_id?: number;
  login?: string;
  notes?: string;
}

// CRUD интерфейсы для администраторов
export interface AdministratorCreate {
  name: string;
  role_id: number;
  status?: string;
  login: string;
  password: string;
  notes?: string;
}

export interface AdministratorUpdate {
  name?: string;
  role_id?: number;
  status?: string;
  login?: string;
  notes?: string;
}

export const usersApi = {
  // Мастера
  getMasters: async (): Promise<Master[]> => {
    const response = await apiClient.get('/users/masters/');
    return response.data;
  },

  getMaster: async (id: number): Promise<Master> => {
    const response = await apiClient.get(`/users/masters/${id}`);
    return response.data;
  },

  createMaster: async (master: MasterCreate): Promise<Master> => {
    const response = await apiClient.post('/users/masters/', master);
    return response.data;
  },

  updateMaster: async (id: number, master: MasterUpdate): Promise<Master> => {
    const response = await apiClient.put(`/users/masters/${id}`, master);
    return response.data;
  },

  deleteMaster: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/users/masters/${id}`);
    return response.data;
  },

  // Сотрудники
  getEmployees: async (): Promise<Employee[]> => {
    const response = await apiClient.get('/users/employees/');
    return response.data;
  },

  getEmployee: async (id: number): Promise<Employee> => {
    const response = await apiClient.get(`/users/employees/${id}`);
    return response.data;
  },

  createEmployee: async (employee: EmployeeCreate): Promise<Employee> => {
    const response = await apiClient.post('/users/employees/', employee);
    return response.data;
  },

  updateEmployee: async (id: number, employee: EmployeeUpdate): Promise<Employee> => {
    const response = await apiClient.put(`/users/employees/${id}`, employee);
    return response.data;
  },

  deleteEmployee: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/users/employees/${id}`);
    return response.data;
  },

  // Администраторы
  getAdministrators: async (): Promise<Administrator[]> => {
    const response = await apiClient.get('/users/administrators/');
    return response.data;
  },

  getAdministrator: async (id: number): Promise<Administrator> => {
    const response = await apiClient.get(`/users/administrators/${id}`);
    return response.data;
  },

  createAdministrator: async (administrator: AdministratorCreate): Promise<Administrator> => {
    const response = await apiClient.post('/users/administrators/', administrator);
    return response.data;
  },

  updateAdministrator: async (id: number, administrator: AdministratorUpdate): Promise<Administrator> => {
    const response = await apiClient.put(`/users/administrators/${id}`, administrator);
    return response.data;
  },

  deleteAdministrator: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/users/administrators/${id}`);
    return response.data;
  },

  // Справочные данные
  getCities: async (): Promise<City[]> => {
    const response = await apiClient.get('/users/cities/');
    return response.data;
  },

  getRoles: async (): Promise<Role[]> => {
    const response = await apiClient.get('/users/roles/');
    return response.data;
  },
}; 