import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import { usersApi, type City, type Role } from '../api/users';
import { requestsApi, type RequestType, type Direction } from '../api/requests';
import { transactionsApi } from '../api/transactions';
import type { TransactionType } from '../types/api';
import { useNotification } from './NotificationContext';

interface AppDataContextType {
  // Справочники
  cities: City[];
  roles: Role[];
  requestTypes: RequestType[];
  directions: Direction[];
  transactionTypes: TransactionType[];
  
  // Состояния загрузки
  loading: {
    cities: boolean;
    roles: boolean;
    requestTypes: boolean;
    directions: boolean;
    transactionTypes: boolean;
  };
  
  // Методы для обновления
  refetchCities: () => Promise<void>;
  refetchRoles: () => Promise<void>;
  refetchRequestTypes: () => Promise<void>;
  refetchDirections: () => Promise<void>;
  refetchTransactionTypes: () => Promise<void>;
  refetchAll: () => Promise<void>;
}

const AppDataContext = createContext<AppDataContextType | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components
export const useAppData = () => {
  const context = useContext(AppDataContext);
  if (!context) {
    throw new Error('useAppData must be used within an AppDataProvider');
  }
  return context;
};

interface AppDataProviderProps {
  children: ReactNode;
}

export const AppDataProvider: React.FC<AppDataProviderProps> = ({ children }) => {
  const [cities, setCities] = useState<City[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
  const [directions, setDirections] = useState<Direction[]>([]);
  const [transactionTypes, setTransactionTypes] = useState<TransactionType[]>([]);
  
  const [loading, setLoading] = useState({
    cities: true,
    roles: true,
    requestTypes: true,
    directions: true,
    transactionTypes: true
  });
  
  const { showError } = useNotification();

  const updateLoading = useCallback((key: keyof typeof loading, value: boolean) => {
    setLoading(prev => ({ ...prev, [key]: value }));
  }, []);

  const refetchCities = useCallback(async () => {
    try {
      updateLoading('cities', true);
      const data = await usersApi.getCities();
      setCities(data);
    } catch (error) {
      showError('Ошибка загрузки городов');
      console.error('Error fetching cities:', error);
    } finally {
      updateLoading('cities', false);
    }
  }, [updateLoading, showError]);

  const refetchRoles = useCallback(async () => {
    try {
      updateLoading('roles', true);
      const data = await usersApi.getRoles();
      setRoles(data);
    } catch (error) {
      showError('Ошибка загрузки ролей');
      console.error('Error fetching roles:', error);
    } finally {
      updateLoading('roles', false);
    }
  }, [updateLoading, showError]);

  const refetchRequestTypes = useCallback(async () => {
    try {
      updateLoading('requestTypes', true);
      const data = await requestsApi.getRequestTypes();
      setRequestTypes(data);
    } catch (error) {
      showError('Ошибка загрузки типов заявок');
      console.error('Error fetching request types:', error);
    } finally {
      updateLoading('requestTypes', false);
    }
  }, [updateLoading, showError]);

  const refetchDirections = useCallback(async () => {
    try {
      updateLoading('directions', true);
      const data = await requestsApi.getDirections();
      setDirections(data);
    } catch (error) {
      showError('Ошибка загрузки направлений');
      console.error('Error fetching directions:', error);
    } finally {
      updateLoading('directions', false);
    }
  }, [updateLoading, showError]);

  const refetchTransactionTypes = useCallback(async () => {
    try {
      updateLoading('transactionTypes', true);
      const data = await transactionsApi.getTransactionTypes();
      setTransactionTypes(data);
    } catch (error) {
      showError('Ошибка загрузки типов транзакций');
      console.error('Error fetching transaction types:', error);
    } finally {
      updateLoading('transactionTypes', false);
    }
  }, [updateLoading, showError]);

  const refetchAll = useCallback(async () => {
    await Promise.all([
      refetchCities(),
      refetchRoles(),
      refetchRequestTypes(),
      refetchDirections(),
      refetchTransactionTypes()
    ]);
  }, [refetchCities, refetchRoles, refetchRequestTypes, refetchDirections, refetchTransactionTypes]);

  // Загружаем все справочники при инициализации
  useEffect(() => {
    refetchAll();
  }, [refetchAll]);

  const value: AppDataContextType = {
    cities,
    roles,
    requestTypes,
    directions,
    transactionTypes,
    loading,
    refetchCities,
    refetchRoles,
    refetchRequestTypes,
    refetchDirections,
    refetchTransactionTypes,
    refetchAll
  };

  return (
    <AppDataContext.Provider value={value}>
      {children}
    </AppDataContext.Provider>
  );
}; 