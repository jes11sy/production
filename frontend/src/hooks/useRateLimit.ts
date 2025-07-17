import React, { useState, useCallback, useRef } from 'react';
import { useNotification } from '../contexts/NotificationContext';

interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
  blockDurationMs?: number;
  onLimitExceeded?: (resetTime: number) => void;
}

interface RateLimitState {
  requests: number[];
  isBlocked: boolean;
  resetTime: number;
}

// Хук для rate limiting
export const useRateLimit = (config: RateLimitConfig) => {
  const { showError, showWarning } = useNotification();
  const [state, setState] = useState<RateLimitState>({
    requests: [],
    isBlocked: false,
    resetTime: 0
  });
  
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  
  const {
    maxRequests,
    windowMs,
    blockDurationMs = windowMs,
    onLimitExceeded
  } = config;
  
  const checkRateLimit = useCallback(() => {
    const now = Date.now();
    
    // Удаляем старые запросы
    const recentRequests = state.requests.filter(
      timestamp => now - timestamp < windowMs
    );
    
    // Проверяем блокировку
    if (state.isBlocked && now < state.resetTime) {
      const remainingTime = Math.ceil((state.resetTime - now) / 1000);
      showWarning(`Слишком много запросов. Попробуйте через ${remainingTime} сек.`);
      return false;
    }
    
    // Если блокировка истекла, сбрасываем состояние
    if (state.isBlocked && now >= state.resetTime) {
      setState(prev => ({
        ...prev,
        isBlocked: false,
        resetTime: 0,
        requests: recentRequests
      }));
    }
    
    // Проверяем лимит
    if (recentRequests.length >= maxRequests) {
      const resetTime = now + blockDurationMs;
      
      setState(prev => ({
        ...prev,
        isBlocked: true,
        resetTime,
        requests: recentRequests
      }));
      
      showError('Превышен лимит запросов. Попробуйте позже.');
      
      if (onLimitExceeded) {
        onLimitExceeded(resetTime);
      }
      
      // Устанавливаем таймер для автоматического сброса
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        setState(prev => ({
          ...prev,
          isBlocked: false,
          resetTime: 0
        }));
      }, blockDurationMs);
      
      return false;
    }
    
    // Добавляем текущий запрос
    setState(prev => ({
      ...prev,
      requests: [...recentRequests, now]
    }));
    
    return true;
  }, [state, maxRequests, windowMs, blockDurationMs, onLimitExceeded, showError, showWarning]);
  
  const getRemainingRequests = useCallback(() => {
    const now = Date.now();
    const recentRequests = state.requests.filter(
      timestamp => now - timestamp < windowMs
    );
    
    return Math.max(0, maxRequests - recentRequests.length);
  }, [state.requests, maxRequests, windowMs]);
  
  const getResetTime = useCallback(() => {
    if (state.isBlocked) {
      return state.resetTime;
    }
    
    const now = Date.now();
    const oldestRequest = state.requests[0];
    
    if (oldestRequest) {
      return oldestRequest + windowMs;
    }
    
    return now;
  }, [state.isBlocked, state.resetTime, state.requests, windowMs]);
  
  const reset = useCallback(() => {
    setState({
      requests: [],
      isBlocked: false,
      resetTime: 0
    });
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);
  
  return {
    canMakeRequest: checkRateLimit,
    remainingRequests: getRemainingRequests(),
    isBlocked: state.isBlocked,
    resetTime: getResetTime(),
    reset
  };
};

// Хук для rate limiting с автоматическим применением к функции
export const useRateLimitedFunction = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  config: RateLimitConfig
): T => {
  const { canMakeRequest } = useRateLimit(config);
  
  const rateLimitedFn = useCallback((...args: Parameters<T>) => {
    if (!canMakeRequest()) {
      return Promise.reject(new Error('Rate limit exceeded'));
    }
    
    return fn(...args);
  }, [fn, canMakeRequest]);
  
  return rateLimitedFn as T;
};

// Глобальный rate limiter для API запросов
class GlobalRateLimiter {
  private limits: Map<string, RateLimitState> = new Map();
  private configs: Map<string, RateLimitConfig> = new Map();
  
  setLimit(key: string, config: RateLimitConfig) {
    this.configs.set(key, config);
    if (!this.limits.has(key)) {
      this.limits.set(key, {
        requests: [],
        isBlocked: false,
        resetTime: 0
      });
    }
  }
  
  canMakeRequest(key: string): boolean {
    const config = this.configs.get(key);
    const state = this.limits.get(key);
    
    if (!config || !state) {
      return true;
    }
    
    const now = Date.now();
    
    // Удаляем старые запросы
    const recentRequests = state.requests.filter(
      timestamp => now - timestamp < config.windowMs
    );
    
    // Проверяем блокировку
    if (state.isBlocked && now < state.resetTime) {
      return false;
    }
    
    // Если блокировка истекла, сбрасываем состояние
    if (state.isBlocked && now >= state.resetTime) {
      state.isBlocked = false;
      state.resetTime = 0;
      state.requests = recentRequests;
    }
    
    // Проверяем лимит
    if (recentRequests.length >= config.maxRequests) {
      const resetTime = now + (config.blockDurationMs || config.windowMs);
      
      state.isBlocked = true;
      state.resetTime = resetTime;
      state.requests = recentRequests;
      
      return false;
    }
    
    // Добавляем текущий запрос
    state.requests = [...recentRequests, now];
    
    return true;
  }
  
  getRemainingRequests(key: string): number {
    const config = this.configs.get(key);
    const state = this.limits.get(key);
    
    if (!config || !state) {
      return Infinity;
    }
    
    const now = Date.now();
    const recentRequests = state.requests.filter(
      timestamp => now - timestamp < config.windowMs
    );
    
    return Math.max(0, config.maxRequests - recentRequests.length);
  }
  
  isBlocked(key: string): boolean {
    const state = this.limits.get(key);
    
    if (!state) {
      return false;
    }
    
    return state.isBlocked && Date.now() < state.resetTime;
  }
  
  reset(key: string) {
    const state = this.limits.get(key);
    
    if (state) {
      state.requests = [];
      state.isBlocked = false;
      state.resetTime = 0;
    }
  }
}

export const globalRateLimiter = new GlobalRateLimiter();

// Конфигурации по умолчанию
export const DEFAULT_RATE_LIMITS = {
  // Общие API запросы
  api: {
    maxRequests: 100,
    windowMs: 60000, // 1 минута
    blockDurationMs: 30000 // 30 секунд блокировки
  },
  
  // Авторизация
  auth: {
    maxRequests: 5,
    windowMs: 300000, // 5 минут
    blockDurationMs: 900000 // 15 минут блокировки
  },
  
  // Загрузка файлов
  upload: {
    maxRequests: 10,
    windowMs: 60000, // 1 минута
    blockDurationMs: 60000 // 1 минута блокировки
  },
  
  // Поиск
  search: {
    maxRequests: 30,
    windowMs: 60000, // 1 минута
    blockDurationMs: 10000 // 10 секунд блокировки
  },
  
  // Отправка форм
  forms: {
    maxRequests: 20,
    windowMs: 60000, // 1 минута
    blockDurationMs: 30000 // 30 секунд блокировки
  }
};

// Инициализация глобальных лимитов
Object.entries(DEFAULT_RATE_LIMITS).forEach(([key, config]) => {
  globalRateLimiter.setLimit(key, config);
});

// Middleware для axios
export const createRateLimitInterceptor = (key: string) => {
  return {
    request: (config: Record<string, unknown>) => {
      if (!globalRateLimiter.canMakeRequest(key)) {
        return Promise.reject(new Error('Rate limit exceeded'));
      }
      
      return config;
    },
    
    response: (response: Record<string, unknown>) => response,
    
    error: (error: { response?: { status?: number; headers?: Record<string, string> } }) => {
      // Если получили 429 (Too Many Requests), обновляем локальный лимит
      if (error.response?.status === 429) {
        const retryAfter = error.response.headers?.['retry-after'];
        if (retryAfter) {
          const blockDuration = parseInt(retryAfter) * 1000;
          const state = globalRateLimiter['limits'].get(key);
          if (state) {
            state.isBlocked = true;
            state.resetTime = Date.now() + blockDuration;
          }
        }
      }
      
      return Promise.reject(error);
    }
  };
};

// Хук для отслеживания состояния rate limit
export const useRateLimitStatus = (key: string) => {
  const [status, setStatus] = useState({
    remainingRequests: globalRateLimiter.getRemainingRequests(key),
    isBlocked: globalRateLimiter.isBlocked(key)
  });
  
  const updateStatus = useCallback(() => {
    setStatus({
      remainingRequests: globalRateLimiter.getRemainingRequests(key),
      isBlocked: globalRateLimiter.isBlocked(key)
    });
  }, [key]);
  
  // Обновляем статус каждые 5 секунд
  const intervalRef = useRef<NodeJS.Timeout | undefined>(undefined);
  
  React.useEffect(() => {
    updateStatus();
    
    intervalRef.current = setInterval(updateStatus, 5000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [updateStatus]);
  
  return {
    ...status,
    refresh: updateStatus
  };
}; 