import { useState, useEffect, useCallback, useRef } from 'react';
import { useNotification } from '../contexts/NotificationContext';

export interface ApiDataState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export interface UseApiDataOptions<T = unknown> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  errorMessage?: string;
}

export function useApiData<T>(
  apiFunction: () => Promise<T>,
  options: UseApiDataOptions<T> = {}
): ApiDataState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { showError } = useNotification();

  const {
    immediate = true,
    onSuccess,
    onError,
    errorMessage = 'Ошибка загрузки данных'
  } = options;

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await apiFunction();
      setData(result);
      
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : errorMessage;
      setError(errorMsg);
      showError(errorMsg);
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMsg));
      }
    } finally {
      setLoading(false);
    }
  }, [apiFunction, onSuccess, onError, errorMessage, showError]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [fetchData, immediate]);

  return {
    data,
    loading,
    error,
    refetch: fetchData
  };
}

// Хук для загрузки нескольких источников данных параллельно
export function useMultipleApiData<T extends Record<string, unknown>>(
  apiCalls: { [K in keyof T]: () => Promise<T[K]> },
  options: UseApiDataOptions = {}
): ApiDataState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { showError } = useNotification();
  
  // Используем ref для стабилизации apiCalls
  const apiCallsRef = useRef(apiCalls);
  apiCallsRef.current = apiCalls;

  const {
    immediate = true,
    onSuccess,
    onError,
    errorMessage = 'Ошибка загрузки данных'
  } = options;

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const keys = Object.keys(apiCallsRef.current) as (keyof T)[];
      const promises = keys.map(key => apiCallsRef.current[key]());
      
      const results = await Promise.all(promises);
      
      const combinedData = keys.reduce((acc, key, index) => {
        acc[key] = results[index];
        return acc;
      }, {} as T);
      
      setData(combinedData);
      
      if (onSuccess) {
        onSuccess(combinedData);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : errorMessage;
      setError(errorMsg);
      showError(errorMsg);
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMsg));
      }
    } finally {
      setLoading(false);
    }
  }, [onSuccess, onError, errorMessage, showError]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [fetchData, immediate]);

  return {
    data,
    loading,
    error,
    refetch: fetchData
  };
}

// Хук для операций с данными (создание, обновление, удаление)
export function useApiMutation<TData, TVariables = void>(
  mutationFunction: (variables: TVariables) => Promise<TData>,
  options: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables) => void;
    successMessage?: string;
    errorMessage?: string;
  } = {}
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { showSuccess, showError } = useNotification();

  const {
    onSuccess,
    onError,
    successMessage,
    errorMessage = 'Ошибка выполнения операции'
  } = options;

  const mutate = useCallback(async (variables: TVariables) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await mutationFunction(variables);
      
      if (successMessage) {
        showSuccess(successMessage);
      }
      
      if (onSuccess) {
        onSuccess(result, variables);
      }
      
      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : errorMessage;
      setError(errorMsg);
      showError(errorMsg);
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMsg), variables);
      }
      
      throw err;
    } finally {
      setLoading(false);
    }
  }, [mutationFunction, onSuccess, onError, successMessage, errorMessage, showSuccess, showError]);

  return {
    mutate,
    loading,
    error
  };
} 