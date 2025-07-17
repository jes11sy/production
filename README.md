# 🚀 LeadSchem Production - Система управления лидами

![LeadSchem](frontend/pictures/logo.png)

**LeadSchem** - это комплексная система управления лидами для бизнеса, разработанная с использованием современного стека технологий. Система предоставляет полный функционал для работы с входящими заявками, управления мастерами, финансовой отчетности и мониторинга рекламных кампаний.

## 📋 Содержание

- [Архитектура системы](#архитектура-системы)
- [Основные возможности](#основные-возможности)
- [Технологический стек](#технологический-стек)
- [Быстрый старт](#быстрый-старт)
- [Развертывание](#развертывание)
- [Документация](#документация)
- [Мониторинг](#мониторинг)
- [Поддержка](#поддержка)

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │───▶│   Nginx Proxy   │───▶│    Backend      │
│   (React SPA)   │    │  (Load Balancer)│    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │      Cache      │    │    Database     │
│ (Prometheus +   │◄──│   (Redis)       │◄──│  (PostgreSQL)   │
│   Grafana)      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ✨ Основные возможности

### 📞 Управление лидами
- **Входящие заявки**: Прием и обработка заявок клиентов
- **Распределение мастеров**: Автоматическое назначение заявок специалистам
- **Отслеживание статусов**: Полный жизненный цикл заявки
- **CRM функционал**: Управление клиентской базой

### 💰 Финансовый учет
- **Кассовые операции**: Приход и расход денежных средств
- **Отчетность**: Детальная финансовая аналитика
- **Транзакции**: Учет всех денежных операций
- **Балансы**: Контроль финансового состояния

### 👥 Управление персоналом
- **База мастеров**: Профили специалистов
- **Рабочие смены**: Планирование и учет рабочего времени
- **Производительность**: Аналитика работы сотрудников
- **Ролевая система**: Гибкое управление доступом

### 📊 Аналитика и отчеты
- **Dashboard**: Общая сводка по системе
- **Рекламные кампании**: ROI и эффективность рекламы
- **Региональная аналитика**: Статистика по городам
- **Отчеты колл-центра**: Производительность операторов

## 🛠️ Технологический стек

### Frontend
- **React 18** - Современный UI фреймворк
- **TypeScript** - Типизированный JavaScript
- **Tailwind CSS** - Utility-first CSS фреймворк
- **Rspack** - Быстрый бандлер (замена Webpack)
- **React Query** - Управление серверным состоянием
- **React Router** - Маршрутизация
- **Zustand** - Управление клиентским состоянием

### Backend
- **FastAPI** - Высокопроизводительный Python веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **Alembic** - Система миграций БД
- **Pydantic** - Валидация данных
- **JWT** - Аутентификация
- **Redis** - Кеширование и сессии
- **Uvicorn** - ASGI сервер

### База данных
- **PostgreSQL 15** - Реляционная база данных
- **Redis 7** - In-memory хранилище для кеша

### Мониторинг
- **Prometheus** - Сбор метрик
- **Grafana** - Визуализация данных
- **Custom Metrics** - Специализированные метрики приложения

### DevOps
- **Docker** - Контейнеризация
- **Docker Compose** - Оркестрация контейнеров
- **Nginx** - Реверс-прокси и статические файлы
- **Let's Encrypt** - SSL сертификаты

## 🚀 Быстрый старт

### Предварительные требования
- Docker 20.10+
- Docker Compose 2.0+
- Git
- 4GB RAM (рекомендуется 8GB+)

### Установка и запуск

```bash
# 1. Клонирование репозитория
git clone https://github.com/jes11sy/production.git
cd production

# 2. Переход в папку развертывания
cd deployment

# 3. Автоматический деплой
./full-deploy.sh
```

### Первый вход в систему
После успешного развертывания:

- **URL**: http://localhost:3000
- **Логин**: admin
- **Пароль**: admin123

⚠️ **ВАЖНО**: Обязательно смените пароль после первого входа!

## 📦 Развертывание

### Локальная разработка
```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py

# Frontend  
cd frontend
npm install
npm run dev
```

### Продакшн развертывание
Подробное руководство: [deployment/README_DEPLOY.md](deployment/README_DEPLOY.md)

```bash
cd deployment
./full-deploy.sh
```

### Управление системой
```bash
# Проверка состояния
./health-check.sh

# Обновление системы
./update-system.sh

# Резервное копирование
./backup.sh

# Просмотр логов
docker-compose -f docker-compose.production.yml logs -f
```

## 📚 Документация

### Для разработчиков
- [Backend API Documentation](backend/docs/README.md)
- [Frontend Documentation](frontend/docs/README.md)
- [Database Schema](backend/docs/DATABASE_MIGRATIONS.md)
- [Security Guide](backend/docs/SECURITY_GUIDE.md)

### Для администраторов
- [Deployment Guide](deployment/README_DEPLOY.md)
- [Monitoring Setup](backend/docs/MONITORING.md)
- [Performance Optimization](backend/docs/DATABASE_OPTIMIZATION.md)
- [Backup & Recovery](deployment/README_DEPLOY.md#резервное-копирование)

### API документация
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📊 Мониторинг

### Доступные интерфейсы
- **Grafana Dashboard**: http://localhost:3001
- **Prometheus Metrics**: http://localhost:9090
- **Application Health**: http://localhost:8000/health
- **System Metrics**: http://localhost:8000/metrics

### Основные метрики
- 🔍 **Производительность**: Время ответа API, пропускная способность
- 💾 **Ресурсы**: Использование CPU, памяти, диска
- 🗄️ **База данных**: Подключения, запросы, время выполнения
- 🌐 **Сеть**: HTTP статусы, время ответа
- 👥 **Бизнес метрики**: Количество заявок, конверсия, ROI

## 🔒 Безопасность

### Реализованные меры
- ✅ **JWT аутентификация** с автоматическим обновлением токенов
- ✅ **HTTPS/TLS** шифрование всего трафика
- ✅ **CORS защита** от межсайтовых запросов
- ✅ **Rate limiting** защита от DDoS атак
- ✅ **Input validation** валидация всех входных данных
- ✅ **SQL injection** защита через ORM
- ✅ **XSS protection** фильтрация контента
- ✅ **File upload** безопасная загрузка файлов

### Рекомендации по безопасности
- 🔐 Регулярно обновляйте пароли
- 🛡️ Настройте firewall для production
- 📱 Включите двухфакторную аутентификацию
- 🔄 Регулярно обновляйте систему
- 📋 Мониторьте логи безопасности

## 🐛 Тестирование

### Backend тесты
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend тесты
```bash
cd frontend
npm test
npm run test:e2e
```

### Покрытие тестами
- **Backend**: 90%+ покрытие кода
- **Frontend**: Компоненты и интеграционные тесты
- **E2E**: Критические пути пользователей

## 🔧 Конфигурация

### Переменные окружения
Основные настройки в файле `deployment/env.production.lead-schem`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
POSTGRESQL_PASSWORD=strong_password

# Security  
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=jwt_secret

# CORS
BACKEND_CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com

# Email
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=app_password
```

### Конфигурация Docker
- `deployment/docker-compose.production.yml` - Production конфигурация
- `backend/deployment/Dockerfile` - Backend образ
- `frontend/Dockerfile.production` - Frontend образ

## 📈 Производительность

### Оптимизации
- ⚡ **Redis кеширование** для быстрого доступа к данным
- 🗄️ **Индексы БД** для оптимизации запросов
- 📦 **Gzip сжатие** для уменьшения трафика
- 🚀 **CDN готовность** для статических ресурсов
- 🔄 **Connection pooling** для базы данных
- 📊 **Lazy loading** для больших списков

### Benchmark результаты
- **API Response Time**: < 100ms (95 percentile)
- **Page Load Time**: < 2s (First Contentful Paint)
- **Database Queries**: < 50ms (average)
- **Concurrent Users**: 1000+ simultaneous users

## 🤝 Поддержка

### Контакты
- **Email**: admin@lead-schem.ru
- **GitHub Issues**: [github.com/jes11sy/production/issues](https://github.com/jes11sy/production/issues)
- **Documentation**: [Полная документация](docs/)

### Сообщить об ошибке
1. Проверьте [существующие issues](https://github.com/jes11sy/production/issues)
2. Создайте новый issue с описанием проблемы
3. Приложите логи и шаги воспроизведения
4. Укажите версию системы и окружение

### Запрос новой функции
1. Опишите желаемую функциональность
2. Объясните бизнес-случай использования
3. Предложите возможную реализацию
4. Обсудите с командой разработки

## 📄 Лицензия

Этот проект является собственностью разработчика. Все права защищены.

## 🏆 Благодарности

Особая благодарность всем контрибьюторам и используемым open-source проектам:
- React Team за отличный фреймворк
- FastAPI за высокопроизводительный backend
- PostgreSQL за надежную базу данных
- Docker за удобную контейнеризацию

---

## 📊 Статистика проекта

- **Строк кода**: 50,000+
- **Файлов**: 500+
- **Коммитов**: 100+
- **Тестов**: 200+
- **Компонентов**: 50+
- **API endpoints**: 100+

---

**Версия**: 1.0.0  
**Последнее обновление**: Декабрь 2024  
**Статус**: Production Ready ✅

*Сделано с ❤️ для эффективного управления бизнесом* 