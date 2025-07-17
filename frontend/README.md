# CRM Frontend

Современный фронтенд для CRM системы, построенный на React 19.1.0 с TypeScript.

## 🚀 Технологии

- **React 19.1.0** - основная библиотека
- **TypeScript** - типизация
- **Rspack** - сборщик (основной)
- **Vite** - альтернативный сборщик
- **HeroUI** - компоненты интерфейса
- **React Router DOM** - маршрутизация
- **Zustand** - управление состоянием
- **Tailwind CSS** - стилизация
- **React Hook Form** - работа с формами
- **TanStack Query** - управление данными

## 🛠️ Установка

```bash
npm install
```

## 📦 Команды

### Основные команды (Rspack)
```bash
npm run dev      # Запуск dev сервера
npm run build    # Production сборка
```

### Альтернативные команды
```bash
npm run dev:vite         # Vite dev сервер
npm run build:vite       # Vite сборка
npm run build:production # Альтернативная сборка
npm run start:production # Express сервер
```

### Утилиты
```bash
npm run typecheck # Проверка TypeScript
npm run lint      # Проверка ESLint
npm run preview   # Предпросмотр сборки
```

## 🏗️ Структура проекта

```
src/
├── api/           # API клиенты
├── components/    # Переиспользуемые компоненты
├── contexts/      # React контексты
├── hooks/         # Кастомные хуки
├── pages/         # Страницы приложения
├── services/      # Сервисы
├── stores/        # Zustand стор
├── types/         # TypeScript типы
└── utils/         # Утилиты
```

## 📚 Документация

Подробная документация находится в папке `docs/`:

- [Отчет о миграции на Rspack](docs/RSPACK_MIGRATION_REPORT.md)
- [Финальный аудит](docs/FINAL_AUDIT_REPORT.md)
- [Отчет о продакшене](docs/PRODUCTION_REPORT.md)
- [Инструкции для продакшена](docs/PRODUCTION_README.md)

## 🔧 Конфигурация

- `rspack.config.cjs` - основная конфигурация сборки
- `vite.config.ts` - конфигурация Vite
- `tailwind.config.cjs` - конфигурация Tailwind
- `tsconfig.json` - конфигурация TypeScript

## 🚀 Продакшен

Проект готов к продакшену. Используйте:

```bash
npm run build
```

Для альтернативной сборки:

```bash
npm run build:production
npm run start:production
```

## 📊 Статус

✅ **Готов к продакшену**
- 0 TypeScript ошибок
- Рабочая сборка с Rspack
- Альтернативное решение с Express
- Полная документация

## 🤝 Разработка

1. Клонируйте репозиторий
2. Установите зависимости: `npm install`
3. Запустите dev сервер: `npm run dev`
4. Откройте http://localhost:3000

---

*Последнее обновление: 16.07.2025* 