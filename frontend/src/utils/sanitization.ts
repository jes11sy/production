import React from 'react';

// Функция для экранирования HTML символов
export const escapeHtml = (text: string): string => {
  if (typeof text !== 'string') return '';
  
  const htmlEscapes: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  };
  
  return text.replace(/[&<>"'/]/g, (match) => htmlEscapes[match]);
};

// Функция для удаления HTML тегов
export const stripHtml = (text: string): string => {
  if (typeof text !== 'string') return '';
  return text.replace(/<[^>]*>/g, '');
};

// Функция для санитизации текста
export const sanitizeText = (text: string, options: {
  allowHtml?: boolean;
  maxLength?: number;
  trim?: boolean;
} = {}): string => {
  if (typeof text !== 'string') return '';
  
  const {
    allowHtml = false,
    maxLength,
    trim = true
  } = options;
  
  let sanitized = text;
  
  // Обрезаем пробелы
  if (trim) {
    sanitized = sanitized.trim();
  }
  
  // Удаляем или экранируем HTML
  if (!allowHtml) {
    sanitized = stripHtml(sanitized);
  } else {
    sanitized = escapeHtml(sanitized);
  }
  
  // Ограничиваем длину
  if (maxLength && sanitized.length > maxLength) {
    sanitized = sanitized.substring(0, maxLength);
  }
  
  return sanitized;
};

// Функция для санитизации номера телефона
export const sanitizePhoneNumber = (phone: string): string => {
  if (typeof phone !== 'string') return '';
  
  // Удаляем все кроме цифр и знака +
  const cleaned = phone.replace(/[^\d+]/g, '');
  
  // Проверяем базовый формат
  if (cleaned.length === 0) return '';
  
  // Если начинается с 8, заменяем на +7
  if (cleaned.startsWith('8') && cleaned.length === 11) {
    return '+7' + cleaned.substring(1);
  }
  
  // Если начинается с 7, добавляем +
  if (cleaned.startsWith('7') && cleaned.length === 11) {
    return '+' + cleaned;
  }
  
  // Если уже есть +, оставляем как есть
  if (cleaned.startsWith('+')) {
    return cleaned;
  }
  
  // Для остальных случаев просто возвращаем очищенный номер
  return cleaned;
};

// Функция для санитизации email
export const sanitizeEmail = (email: string): string => {
  if (typeof email !== 'string') return '';
  
  return email.toLowerCase().trim();
};

// Функция для санитизации URL
export const sanitizeUrl = (url: string): string => {
  if (typeof url !== 'string') return '';
  
  const trimmed = url.trim();
  
  // Проверяем на допустимые протоколы
  const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
  
  try {
    const urlObj = new URL(trimmed);
    if (allowedProtocols.includes(urlObj.protocol)) {
      return trimmed;
    }
  } catch {
    // Если URL невалидный, возвращаем пустую строку
    return '';
  }
  
  return '';
};

// Функция для санитизации объекта
export const sanitizeObject = <T extends Record<string, unknown>>(
  obj: T,
  rules: Partial<Record<keyof T, {
    type: 'text' | 'email' | 'phone' | 'url' | 'number';
    maxLength?: number;
    allowHtml?: boolean;
    required?: boolean;
  }>> = {}
): T => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sanitized = { ...obj } as any;
  
  Object.keys(sanitized).forEach(key => {
    const rule = rules[key as keyof T];
    const value = sanitized[key];
    
    if (rule && value !== null && value !== undefined) {
      switch (rule.type) {
        case 'text':
          sanitized[key] = sanitizeText(String(value), {
            allowHtml: rule.allowHtml,
            maxLength: rule.maxLength
          });
          break;
        case 'email':
          sanitized[key] = sanitizeEmail(String(value));
          break;
        case 'phone':
          sanitized[key] = sanitizePhoneNumber(String(value));
          break;
        case 'url':
          sanitized[key] = sanitizeUrl(String(value));
          break;
        case 'number': {
          const num = Number(value);
          sanitized[key] = isNaN(num) ? 0 : num;
          break;
        }
      }
    }
  });
  
  return sanitized as T;
};

// Компонент для безопасного отображения текста
export const SafeText: React.FC<{
  text: string;
  maxLength?: number;
  showTooltip?: boolean;
  className?: string;
}> = ({ text, maxLength, showTooltip = true, className = '' }) => {
  const sanitized = sanitizeText(text, { maxLength });
  const isTruncated = maxLength && text.length > maxLength;
  
  if (showTooltip && isTruncated) {
    return React.createElement('span', {
      className,
      title: sanitizeText(text)
    }, sanitized + '...');
  }
  
  return React.createElement('span', { className }, sanitized);
};

// Хук для санитизации данных формы
export const useSanitizedForm = <T extends Record<string, unknown>>(
  initialData: T,
  sanitizationRules: Partial<Record<keyof T, {
    type: 'text' | 'email' | 'phone' | 'url' | 'number';
    maxLength?: number;
    allowHtml?: boolean;
    required?: boolean;
  }>> = {}
) => {
  const [data, setData] = React.useState<T>(initialData);
  
  const updateField = React.useCallback((field: keyof T, value: T[keyof T]) => {
    setData(prev => {
      const updated = { ...prev, [field]: value };
      return sanitizeObject(updated, sanitizationRules);
    });
  }, [sanitizationRules]);
  
  const sanitizeAllFields = React.useCallback(() => {
    setData(prev => sanitizeObject(prev, sanitizationRules));
  }, [sanitizationRules]);
  
  return {
    data,
    updateField,
    sanitizeAllFields,
    setData: (newData: T) => setData(sanitizeObject(newData, sanitizationRules))
  };
};

// Валидатор для проверки на потенциально опасный контент
export const validateSafeContent = (content: string): {
  isValid: boolean;
  issues: string[];
} => {
  const issues: string[] = [];
  
  // Проверка на скрипты
  if (/<script[^>]*>.*<\/script>/gi.test(content)) {
    issues.push('Обнаружен JavaScript код');
  }
  
  // Проверка на потенциально опасные атрибуты
  if (/on\w+\s*=/gi.test(content)) {
    issues.push('Обнаружены event handlers');
  }
  
  // Проверка на iframe
  if (/<iframe[^>]*>/gi.test(content)) {
    issues.push('Обнаружен iframe');
  }
  
  // Проверка на потенциально опасные протоколы
  if (/javascript:|data:|vbscript:/gi.test(content)) {
    issues.push('Обнаружены опасные протоколы');
  }
  
  return {
    isValid: issues.length === 0,
    issues
  };
};

// Функция для создания безопасного HTML (если действительно нужно)
export const createSafeHtml = (html: string): string => {
  // Простая реализация whitelist фильтра
  let safe = html;
  
  // Удаляем все теги кроме разрешенных
  safe = safe.replace(/<(?!\/?(?:p|br|strong|em|u|ol|ul|li|a)\b)[^>]*>/gi, '');
  
  // Удаляем опасные атрибуты
  safe = safe.replace(/(<[^>]+)\s+(on\w+|style|class)\s*=\s*["'][^"']*["']/gi, '$1');
  
  // Проверяем href атрибуты
  safe = safe.replace(/href\s*=\s*["']([^"']*)["']/gi, (_, url) => {
    const sanitizedUrl = sanitizeUrl(url);
    return sanitizedUrl ? `href="${sanitizedUrl}"` : '';
  });
  
  return safe;
};

// Дополнительные утилиты для файлов
export const sanitizeFileName = (fileName: string): string => {
  if (typeof fileName !== 'string') return '';
  
  // Удаляем опасные символы
  let safe = fileName.replace(/[<>:"/\\|?*]/g, '');
  
  // Удаляем контрольные символы (ASCII 0-31 и 127-159)
  safe = safe.split('').filter(char => {
    const code = char.charCodeAt(0);
    return code >= 32 && code <= 126 || code >= 160;
  }).join('');
  
  // Ограничиваем длину
  const maxLength = 255;
  return safe.length > maxLength ? safe.substring(0, maxLength) : safe;
};

export const validateFileType = (fileName: string, allowedTypes: string[]): boolean => {
  if (typeof fileName !== 'string') return false;
  
  const extension = fileName.split('.').pop()?.toLowerCase();
  if (!extension) return false;
  
  return allowedTypes.includes(extension);
};

// Константы для безопасности
export const SECURITY_LIMITS = {
  MAX_TEXT_LENGTH: 10000,
  MAX_FILENAME_LENGTH: 255,
  MAX_URL_LENGTH: 2048,
  MAX_EMAIL_LENGTH: 254,
  MAX_PHONE_LENGTH: 20,
  ALLOWED_FILE_TYPES: ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'mp3', 'mp4'],
  ALLOWED_IMAGE_TYPES: ['jpg', 'jpeg', 'png', 'gif'],
  ALLOWED_DOCUMENT_TYPES: ['pdf', 'doc', 'docx', 'xls', 'xlsx'],
  ALLOWED_MEDIA_TYPES: ['mp3', 'mp4', 'wav', 'avi', 'mov']
}; 