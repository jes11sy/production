# 🧪 Руководство по тестированию Frontend

## 📋 Обзор

Данное руководство описывает настроенную систему тестирования для frontend части CRM системы.

## 🛠 Настроенные инструменты

### 1. **Vitest** - Unit тестирование
- ⚡ Быстрый test runner
- 🔧 Встроенная поддержка TypeScript
- 📊 Coverage отчеты
- 🎯 Совместимость с Jest API

### 2. **Testing Library** - Компонентное тестирование
- 🧪 `@testing-library/react` - тестирование React компонентов
- 🎭 `@testing-library/user-event` - симуляция пользовательских действий
- ✅ `@testing-library/jest-dom` - дополнительные матчеры

### 3. **Playwright** - E2E тестирование
- 🌐 Кросс-браузерное тестирование
- 📱 Мобильные устройства
- 🎥 Запись видео и скриншоты
- 🔍 Автоматическое ожидание элементов

## 📁 Структура тестов

```
frontend/
├── src/
│   └── test/
│       ├── setup.ts              # Настройка тестового окружения
│       └── components/           # Unit тесты компонентов
│           ├── Login.test.tsx
│           ├── Dashboard.test.tsx
│           ├── UsersPage.test.tsx
│           └── SimpleLogin.test.tsx
├── tests/
│   └── e2e/                     # E2E тесты
│       └── login.spec.ts
├── vitest.config.ts             # Конфигурация Vitest
└── playwright.config.ts         # Конфигурация Playwright
```

## 🚀 Команды для запуска тестов

### Unit тесты (Vitest)
```bash
# Запуск в watch режиме
npm run test

# Запуск всех тестов
npm run test:run

# UI интерфейс для тестов
npm run test:ui

# Генерация coverage отчета
npm run test:coverage
```

### E2E тесты (Playwright)
```bash
# Запуск E2E тестов
npm run test:e2e

# Запуск с UI интерфейсом
npm run test:e2e:ui

# Запуск с открытым браузером
npm run test:e2e:headed
```

## 📝 Примеры тестов

### Unit тест компонента
```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(
      <BrowserRouter>
        <MyComponent />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Hello World')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    render(<MyComponent />)
    
    const button = screen.getByRole('button')
    await user.click(button)
    
    expect(screen.getByText('Clicked!')).toBeInTheDocument()
  })
})
```

### E2E тест
```typescript
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  await page.goto('/')
  
  await page.fill('input[name="login"]', 'testuser')
  await page.fill('input[name="password"]', 'password')
  await page.click('button[type="submit"]')
  
  await expect(page).toHaveURL('/dashboard')
})
```

## 🎯 Что протестировано

### ✅ Реализованные тесты
1. **Login компонент**
   - Отображение формы
   - Валидация полей
   - Обработка авторизации
   - Обработка ошибок
   - Переключение видимости пароля

2. **Dashboard компонент**
   - Загрузка данных
   - Отображение статистики
   - Обработка состояний загрузки
   - Расчет метрик

3. **UsersPage компонент**
   - Переключение табов
   - CRUD операции
   - Обработка ошибок
   - Уведомления

4. **E2E тесты**
   - Авторизация пользователя
   - Валидация форм
   - Навигация по приложению

## 🔧 Настройка окружения

### Vitest конфигурация
- **Environment**: jsdom (для DOM тестирования)
- **Globals**: включены для Jest-совместимого API
- **Coverage**: v8 provider
- **Setup**: автоматический импорт jest-dom матчеров

### Моки и фикстуры
```typescript
// Мок API модулей
vi.mock('../api/users', () => ({
  usersApi: {
    getUsers: vi.fn(),
    deleteUser: vi.fn(),
  }
}))

// Мок React Router
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  BrowserRouter: ({ children }) => children,
}))
```

## 📊 Coverage цели

- **Компоненты**: 80%+
- **Утилиты**: 90%+
- **API клиенты**: 70%+
- **Общее покрытие**: 75%+

## 🚨 Проблемы и решения

### Проблема: Сложные моки в Vitest
**Решение**: Использовать `vi.mock()` на верхнем уровне файла

### Проблема: HeroUI компоненты в тестах
**Решение**: Мокировать сложные UI компоненты или использовать реальные

### Проблема: Асинхронные операции
**Решение**: Использовать `waitFor()` и `findBy*` методы

## 🎯 Дальнейшие планы

### Краткосрочные (1-2 недели)
- [ ] Исправить проблемы с моками в Dashboard/UsersPage тестах
- [ ] Добавить тесты для остальных компонентов
- [ ] Настроить автоматический запуск тестов в CI/CD

### Среднесрочные (1-2 месяца)
- [ ] Достичь 80%+ покрытия тестами
- [ ] Добавить visual regression тесты
- [ ] Настроить performance тестирование

### Долгосрочные (3+ месяца)
- [ ] Полное покрытие E2E сценариев
- [ ] Интеграция с мониторингом качества
- [ ] Автоматическая генерация тестов

## 🔗 Полезные ссылки

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Playwright Documentation](https://playwright.dev/)
- [Jest-DOM Matchers](https://github.com/testing-library/jest-dom) 