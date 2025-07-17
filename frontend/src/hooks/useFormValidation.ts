import { useState, useCallback, useMemo } from 'react';
import { useNotification } from '../contexts/NotificationContext';

// Типы для валидации
export interface ValidationRule<T = unknown> {
  required?: boolean;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  email?: boolean;
  phone?: boolean;
  custom?: (value: T) => string | null;
  message?: string;
}

export interface FieldConfig<T = unknown> {
  value: T;
  rules?: ValidationRule<T>;
  touched?: boolean;
  error?: string;
}

export type FormConfig<T extends Record<string, unknown>> = {
  [K in keyof T]: FieldConfig<T[K]>;
};

export interface UseFormValidationResult<T extends Record<string, unknown>> {
  fields: FormConfig<T>;
  errors: Record<keyof T, string>;
  isValid: boolean;
  isSubmitting: boolean;
  setValue: <K extends keyof T>(field: K, value: T[K]) => void;
  setError: <K extends keyof T>(field: K, error: string) => void;
  clearError: <K extends keyof T>(field: K) => void;
  clearAllErrors: () => void;
  validateField: <K extends keyof T>(field: K) => boolean;
  validateForm: () => boolean;
  resetForm: () => void;
  setTouched: <K extends keyof T>(field: K, touched?: boolean) => void;
  handleSubmit: (onSubmit: (data: T) => Promise<void> | void) => (e?: React.FormEvent) => Promise<void>;
  getFieldProps: <K extends keyof T>(field: K) => {
    value: T[K];
    onChange: (value: T[K]) => void;
    onBlur: () => void;
    error: string;
    isInvalid: boolean;
  };
}

// Встроенные валидаторы
const validators = {
  required: (value: unknown): string | null => {
    if (value === null || value === undefined || value === '') {
      return 'Это поле обязательно для заполнения';
    }
    if (Array.isArray(value) && value.length === 0) {
      return 'Это поле обязательно для заполнения';
    }
    return null;
  },

  min: (value: number, min: number): string | null => {
    if (typeof value === 'number' && value < min) {
      return `Значение должно быть больше или равно ${min}`;
    }
    return null;
  },

  max: (value: number, max: number): string | null => {
    if (typeof value === 'number' && value > max) {
      return `Значение должно быть меньше или равно ${max}`;
    }
    return null;
  },

  minLength: (value: string, minLength: number): string | null => {
    if (typeof value === 'string' && value.length < minLength) {
      return `Минимальная длина ${minLength} символов`;
    }
    return null;
  },

  maxLength: (value: string, maxLength: number): string | null => {
    if (typeof value === 'string' && value.length > maxLength) {
      return `Максимальная длина ${maxLength} символов`;
    }
    return null;
  },

  pattern: (value: string, pattern: RegExp): string | null => {
    if (typeof value === 'string' && !pattern.test(value)) {
      return 'Неверный формат';
    }
    return null;
  },

  email: (value: string): string | null => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (typeof value === 'string' && value && !emailRegex.test(value)) {
      return 'Введите корректный email адрес';
    }
    return null;
  },

  phone: (value: string): string | null => {
    const phoneRegex = /^[+]?[1-9][\d]{0,15}$/;
    if (typeof value === 'string' && value && !phoneRegex.test(value.replace(/[\s\-()]/g, ''))) {
      return 'Введите корректный номер телефона';
    }
    return null;
  }
};

export function useFormValidation<T extends Record<string, unknown>>(
  initialValues: T,
  validationRules: Partial<Record<keyof T, ValidationRule<T[keyof T]>>> = {}
): UseFormValidationResult<T> {
  const { showError } = useNotification();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Инициализация полей
  const [fields, setFields] = useState<FormConfig<T>>(() => {
    const initialFields = {} as FormConfig<T>;
    (Object.keys(initialValues) as Array<keyof T>).forEach(key => {
      initialFields[key] = {
        value: initialValues[key],
        rules: validationRules[key],
        touched: false,
        error: ''
      };
    });
    return initialFields;
  });

  // Валидация отдельного поля
  const validateField = useCallback(<K extends keyof T>(field: K): boolean => {
    const fieldConfig = fields[field];
    const rules = fieldConfig.rules;
    
    if (!rules) return true;

    const value = fieldConfig.value;
    let error: string | null = null;

    // Проверка required
    if (rules.required) {
      error = validators.required(value);
      if (error) {
        setFields(prev => ({
          ...prev,
          [field]: { ...prev[field], error }
        }));
        return false;
      }
    }

    // Если поле пустое и не обязательное, пропускаем остальные проверки
    if (!value && !rules.required) {
      setFields(prev => ({
        ...prev,
        [field]: { ...prev[field], error: '' }
      }));
      return true;
    }

    // Остальные проверки
    if (rules.min !== undefined) {
      error = validators.min(value as number, rules.min);
    }
    if (!error && rules.max !== undefined) {
      error = validators.max(value as number, rules.max);
    }
    if (!error && rules.minLength !== undefined) {
      error = validators.minLength(value as string, rules.minLength);
    }
    if (!error && rules.maxLength !== undefined) {
      error = validators.maxLength(value as string, rules.maxLength);
    }
    if (!error && rules.pattern) {
      error = validators.pattern(value as string, rules.pattern);
    }
    if (!error && rules.email) {
      error = validators.email(value as string);
    }
    if (!error && rules.phone) {
      error = validators.phone(value as string);
    }
    if (!error && rules.custom) {
      error = rules.custom(value);
    }

    // Используем кастомное сообщение если есть
    if (error && rules.message) {
      error = rules.message;
    }

    setFields(prev => ({
      ...prev,
      [field]: { ...prev[field], error: error || '' }
    }));

    return !error;
  }, [fields]);

  // Валидация всей формы
  const validateForm = useCallback((): boolean => {
    let isValid = true;
    (Object.keys(fields) as Array<keyof T>).forEach(key => {
      if (!validateField(key)) {
        isValid = false;
      }
    });
    return isValid;
  }, [fields, validateField]);

  // Установка значения поля
  const setValue = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setFields(prev => ({
      ...prev,
      [field]: { ...prev[field], value }
    }));
  }, []);

  // Установка ошибки поля
  const setError = useCallback(<K extends keyof T>(field: K, error: string) => {
    setFields(prev => ({
      ...prev,
      [field]: { ...prev[field], error }
    }));
  }, []);

  // Очистка ошибки поля
  const clearError = useCallback(<K extends keyof T>(field: K) => {
    setFields(prev => ({
      ...prev,
      [field]: { ...prev[field], error: '' }
    }));
  }, []);

  // Очистка всех ошибок
  const clearAllErrors = useCallback(() => {
    setFields(prev => {
      const newFields = { ...prev };
      (Object.keys(newFields) as Array<keyof T>).forEach(key => {
        newFields[key] = { ...newFields[key], error: '' };
      });
      return newFields;
    });
  }, []);

  // Установка touched состояния
  const setTouched = useCallback(<K extends keyof T>(field: K, touched = true) => {
    setFields(prev => ({
      ...prev,
      [field]: { ...prev[field], touched }
    }));
  }, []);

  // Сброс формы
  const resetForm = useCallback(() => {
    setFields(() => {
      const resetFields = {} as FormConfig<T>;
      (Object.keys(initialValues) as Array<keyof T>).forEach(key => {
        resetFields[key] = {
          value: initialValues[key],
          rules: validationRules[key],
          touched: false,
          error: ''
        };
      });
      return resetFields;
    });
    setIsSubmitting(false);
  }, [initialValues, validationRules]);

  // Обработчик отправки формы
  const handleSubmit = useCallback((onSubmit: (data: T) => Promise<void> | void) => {
    return async (e?: React.FormEvent) => {
      if (e) {
        e.preventDefault();
      }

      setIsSubmitting(true);

      try {
        // Валидация формы
        if (!validateForm()) {
          showError('Исправьте ошибки в форме');
          return;
        }

        // Собираем данные
        const formData = {} as T;
        (Object.keys(fields) as Array<keyof T>).forEach(key => {
          formData[key] = fields[key].value;
        });

        // Отправляем
        await onSubmit(formData);
      } catch (error) {
        console.error('Form submission error:', error);
        showError('Ошибка при отправке формы');
      } finally {
        setIsSubmitting(false);
      }
    };
  }, [fields, validateForm, showError]);

  // Получение пропсов для поля
  const getFieldProps = useCallback(<K extends keyof T>(field: K) => {
    const fieldConfig = fields[field];
    return {
      value: fieldConfig.value,
      onChange: (value: T[K]) => setValue(field, value),
      onBlur: () => {
        setTouched(field, true);
        validateField(field);
      },
      error: fieldConfig.error || '',
      isInvalid: !!(fieldConfig.touched && fieldConfig.error)
    };
  }, [fields, setValue, setTouched, validateField]);

  // Вычисляемые значения
  const errors = useMemo(() => {
    const errorMap = {} as Record<keyof T, string>;
    (Object.keys(fields) as Array<keyof T>).forEach(key => {
      errorMap[key] = fields[key].error || '';
    });
    return errorMap;
  }, [fields]);

  const isValid = useMemo(() => {
    return Object.values(fields).every(field => !field.error);
  }, [fields]);

  return {
    fields,
    errors,
    isValid,
    isSubmitting,
    setValue,
    setError,
    clearError,
    clearAllErrors,
    validateField,
    validateForm,
    resetForm,
    setTouched,
    handleSubmit,
    getFieldProps
  };
}

// Готовые правила валидации
export const validationRules = {
  required: { required: true },
  email: { email: true },
  phone: { phone: true },
  minLength: (length: number) => ({ minLength: length }),
  maxLength: (length: number) => ({ maxLength: length }),
  min: (value: number) => ({ min: value }),
  max: (value: number) => ({ max: value }),
  pattern: (pattern: RegExp, message?: string) => ({ pattern, message }),
  custom: (validator: (value: unknown) => string | null) => ({ custom: validator })
}; 