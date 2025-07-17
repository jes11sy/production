// Базовые типы для API
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

// Типы для статусов  
export type RequestStatus = 
  // Английские статусы (legacy)
  | 'new' | 'pending' | 'in_progress' | 'done' | 'completed' | 'cancelled'
  // Русские статусы (текущие)
  | 'Новая' | 'Перезвонить' | 'ТНО' | 'Отказ' | 'В работе' | 'Готово' | 'Принял';
export type TransactionStatus = 'pending' | 'completed' | 'cancelled';
export type UserStatus = 'active' | 'inactive' | 'blocked';
export type MasterStatus = 'active' | 'inactive' | 'busy';

// Базовые сущности
export interface BaseEntity {
  id: number;
  created_at: string;
  updated_at?: string;
}

export interface City extends BaseEntity {
  name: string;
  region?: string;
  is_active: boolean;
}

export interface RequestType extends BaseEntity {
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Direction extends BaseEntity {
  name: string;
  description?: string;
  is_active: boolean;
}

export interface TransactionType extends BaseEntity {
  name: string;
  description?: string;
  is_income: boolean;
  is_active: boolean;
}

// Пользователи
export interface User extends BaseEntity {
  login: string;
  status: UserStatus;
  user_type: 'admin' | 'employee' | 'master';
  role?: string;
  last_login?: string;
}

export interface Master extends BaseEntity {
  city_id: number;
  full_name: string;
  phone_number: string;
  birth_date?: string;
  passport?: string;
  status: MasterStatus;
  chat_id?: string;
  login: string;
  notes?: string;
  city: City;
  user?: User;
}

export interface Employee extends BaseEntity {
  name: string;
  role_id: number;
  status: UserStatus;
  city_id?: number;
  login: string;
  notes?: string;
  role: Role;
  city?: City;
  user?: User;
}

export interface Administrator extends BaseEntity {
  name: string;
  role_id: number;
  status: UserStatus;
  login: string;
  notes?: string;
  role: Role;
  user?: User;
}

export interface Role extends BaseEntity {
  name: string;
  description?: string;
  permissions: string[];
}

// Заявки
export interface Request extends BaseEntity {
  advertising_campaign_id?: number;
  city_id: number;
  request_type_id: number;
  client_phone: string;
  client_name: string;
  address?: string;
  meeting_date?: string;
  direction_id?: number;
  problem?: string;
  status: RequestStatus;
  master_id?: number;
  master_notes?: string;
  result?: string;
  expenses: number;
  net_amount: number;
  master_handover: number;
  ats_number?: string;
  call_center_name?: string;
  call_center_notes?: string;
  avito_chat_id?: string;
  
  // Связанные сущности
  city: City;
  request_type: RequestType;
  direction?: Direction;
  master?: Master;
  advertising_campaign?: AdvertisingCampaign;
  
  // Файлы
  bso_file_path?: string;
  expense_file_path?: string;
  recording_file_path?: string;
}

export interface CreateRequestData {
  advertising_campaign_id?: number;
  city_id: number;
  request_type_id: number;
  client_phone: string;
  client_name: string;
  address?: string;
  meeting_date?: string;
  direction_id?: number;
  problem?: string;
  master_id?: number;
}

export interface UpdateRequestData extends Partial<CreateRequestData> {
  status?: RequestStatus;
  master_notes?: string;
  result?: string;
  expenses?: number;
  net_amount?: number;
  master_handover?: number;
  ats_number?: string;
  call_center_name?: string;
  call_center_notes?: string;
  avito_chat_id?: string;
}

// Транзакции
export interface Transaction extends BaseEntity {
  amount: number;
  description?: string;
  type_id: number;
  city_id: number;
  user_id: number;
  status: TransactionStatus;
  reference_id?: number;
  reference_type?: string;
  
  // Связанные сущности
  type: TransactionType;
  city: City;
  user: User;
}

export interface CreateTransactionData {
  amount: number;
  description?: string;
  type_id: number;
  city_id: number;
  reference_id?: number;
  reference_type?: string;
}

export interface UpdateTransactionData extends Partial<CreateTransactionData> {
  status?: TransactionStatus;
}

// Рекламные кампании
export interface AdvertisingCampaign extends BaseEntity {
  name: string;
  phone_number: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
  is_active?: boolean;
  city_id: number;
  
  // Связанные сущности
  city: City;
}

export interface CreateAdvertisingCampaignData {
  name: string;
  phone_number: string;
  city_id: number;
  description?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
}

export interface UpdateAdvertisingCampaignData extends Partial<CreateAdvertisingCampaignData> {
  is_active?: boolean;
}

// Фильтры для запросов
export interface RequestFilters {
  status?: RequestStatus;
  city_id?: number;
  request_type_id?: number;
  direction_id?: number;
  master_id?: number;
  advertising_campaign_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface TransactionFilters {
  status?: TransactionStatus;
  city_id?: number;
  type_id?: number;
  user_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface UserFilters {
  status?: UserStatus;
  user_type?: string;
  city_id?: number;
  search?: string;
}

// Параметры пагинации
export interface PaginationParams {
  page?: number;
  size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// Типы для форм
export interface FormField<T = unknown> {
  value: T;
  error?: string;
  touched?: boolean;
  required?: boolean;
}

export interface FormState<T extends Record<string, unknown>> {
  fields: { [K in keyof T]: FormField<T[K]> };
  isValid: boolean;
  isSubmitting: boolean;
  errors: Record<string, string>;
}

// Типы для таблиц
export interface TableColumn<T = Record<string, unknown>> {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  render?: (value: unknown, item: T) => React.ReactNode;
}

export interface TableSort {
  column: string;
  direction: 'asc' | 'desc';
}

// Типы для файлов
export interface FileUpload {
  file: File;
  progress: number;
  error?: string;
  url?: string;
}

export interface FileInfo {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
  uploaded_at: string;
} 