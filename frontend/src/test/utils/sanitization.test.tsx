import { describe, it, expect } from 'vitest'

// Простые функции для тестирования
const sanitizeText = (text: string): string => {
  return text.replace(/[<>]/g, '').trim()
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0
  }).format(amount)
}

const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const validatePhone = (phone: string): boolean => {
  const phoneRegex = /^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$/
  return phoneRegex.test(phone)
}

describe('Utility Functions', () => {
  describe('sanitizeText', () => {
    it('should remove dangerous characters', () => {
      const input = '<script>alert("xss")</script>'
      const result = sanitizeText(input)
      
      expect(result).toBe('scriptalert("xss")/script')
      expect(result).not.toContain('<')
      expect(result).not.toContain('>')
    })

    it('should trim whitespace', () => {
      const input = '  hello world  '
      const result = sanitizeText(input)
      
      expect(result).toBe('hello world')
    })

    it('should handle empty string', () => {
      const result = sanitizeText('')
      expect(result).toBe('')
    })
  })

  describe('formatCurrency', () => {
    it('should format positive numbers', () => {
      const result1000 = formatCurrency(1000)
      const result15000 = formatCurrency(15000)
      const result500 = formatCurrency(500)
      
      expect(result1000).toContain('1')
      expect(result1000).toContain('000')
      expect(result1000).toContain('₽')
      
      expect(result15000).toContain('15')
      expect(result15000).toContain('000')
      expect(result15000).toContain('₽')
      
      expect(result500).toContain('500')
      expect(result500).toContain('₽')
    })

    it('should format zero', () => {
      const result = formatCurrency(0)
      expect(result).toContain('0')
      expect(result).toContain('₽')
    })

    it('should format negative numbers', () => {
      const result = formatCurrency(-1000)
      expect(result).toContain('-')
      expect(result).toContain('1')
      expect(result).toContain('000')
      expect(result).toContain('₽')
    })

    it('should handle decimal numbers', () => {
      const result = formatCurrency(1000.5)
      expect(result).toContain('₽')
      // Проверяем что результат содержит цифры
      expect(/\d/.test(result)).toBe(true)
    })
  })

  describe('validateEmail', () => {
    it('should validate correct emails', () => {
      expect(validateEmail('test@example.com')).toBe(true)
      expect(validateEmail('user@domain.ru')).toBe(true)
      expect(validateEmail('admin@company.org')).toBe(true)
    })

    it('should reject invalid emails', () => {
      expect(validateEmail('invalid-email')).toBe(false)
      expect(validateEmail('test@')).toBe(false)
      expect(validateEmail('@domain.com')).toBe(false)
      expect(validateEmail('test.domain.com')).toBe(false)
      expect(validateEmail('')).toBe(false)
    })
  })

  describe('validatePhone', () => {
    it('should validate correct phone format', () => {
      expect(validatePhone('+7(999)123-45-67')).toBe(true)
      expect(validatePhone('+7(495)555-12-34')).toBe(true)
    })

    it('should reject invalid phone formats', () => {
      expect(validatePhone('+79991234567')).toBe(false)
      expect(validatePhone('8(999)123-45-67')).toBe(false)
      expect(validatePhone('+7(999)1234567')).toBe(false)
      expect(validatePhone('invalid-phone')).toBe(false)
      expect(validatePhone('')).toBe(false)
    })
  })
}) 