# 🚀 Отчет по исправлению продакшн конфигурации lead-schem.ru

## 📋 Обзор выполненных исправлений

Проведен полный аудит и исправление конфигурации проекта для корректного развертывания в продакшн окружении на домене **lead-schem.ru**.

### ✅ Критические проблемы, которые были исправлены:

## 1. Backend API CORS Configuration

### Проблема:
Hardcoded `localhost:3000` в CORS headers во всех API файлах

### Решение:
- ✅ Создан utility модуль `backend/app/core/cors_utils.py`
- ✅ Автоматически исправлены файлы:
  - `backend/app/api/auth.py`
  - `backend/app/api/users.py`
  - `backend/app/api/requests.py`
  - `backend/app/api/transactions.py`
- ✅ CORS headers теперь берутся из конфигурации в зависимости от ENVIRONMENT

## 2. Frontend Configuration

### Проблема:
`rspack.config.cjs` использовал localhost:8000 для всех окружений

### Решение:
- ✅ Добавлены условия для продакшн окружения
- ✅ Proxy target автоматически переключается:
  - **Development**: `http://localhost:8000`
  - **Production**: `https://lead-schem.ru`

## 3. Environment Configuration

### Проблема:
Отсутствие корректного .env файла для продакшн

### Решение:
- ✅ Создан `deployment/env.production.lead-schem` с полной конфигурацией
- ✅ Добавлены все необходимые переменные окружения:
  - База данных PostgreSQL
  - Redis конфигурация
  - CORS origins для lead-schem.ru
  - Email настройки (Rambler SMTP)
  - Telegram alerts
  - SSL сертификаты
  - Мониторинг настройки

## 4. Docker Compose Production

### Проблема:
Недостающие переменные окружения в docker-compose.production.yml

### Решение:
- ✅ Добавлены все необходимые переменные окружения
- ✅ Конфигурация безопасности для продакшн
- ✅ Правильные CORS origins

## 5. Monitoring Configuration

### Проблема:
`prometheus.yml` использовал localhost targets

### Решение:
- ✅ Исправлены targets для Docker окружения:
  - `leadschem_backend:8000`
  - `redis:6379`
  - `leadschem_prometheus:9090`
  - `leadschem_postgres:5432`

## 6. API Documentation

### Проблема:
Некорректные server URLs в OpenAPI документации

### Решение:
- ✅ Обновлен `backend/app/api_docs.py`
- ✅ Production server URL: `https://lead-schem.ru/api/v1`

---

## 🔧 Технические детали продакшн окружения

### Сервер:
- **IP**: 194.87.201.221
- **SSH**: `ssh root@194.87.201.221` (пароль: uS6sP4kQpox-_.)
- **Домен**: lead-schem.ru

### База данных:
```bash
# Подключение к PostgreSQL
export PGSSLROOTCERT=$HOME/.cloud-certs/root.crt
psql 'postgresql://gen_user:Jple%24%3F%7Dbl!hCd3@74ac89b6f8cc981b84f28f3b.twc1.net:5432/default_db?sslmode=verify-full'
```

### Redis:
- **Host**: redis (локальный Docker контейнер)
- **Port**: 6379
- **Password**: Fuck2015@@

---

## 📦 Инструкции по развертыванию

### 1. Подготовка сервера

```bash
# Подключение к серверу
ssh root@194.87.201.221

# Переход в директорию приложения
cd /opt/leadschem/

# Остановка текущих контейнеров (если запущены)
docker-compose down
```

### 2. Обновление кода

```bash
# Клонирование/обновление репозитория
git clone <repository-url> .
# или
git pull origin main

# Копирование продакшн конфигурации
cp deployment/env.production.lead-schem .env
```

### 3. Настройка переменных окружения

Проверьте файл `.env` и убедитесь что все переменные корректны:

```bash
nano .env
```

**Основные переменные для проверки:**
- `ENVIRONMENT=production`
- `DOMAIN=lead-schem.ru`
- `DATABASE_URL` (должен содержать правильные данные PostgreSQL)
- `CORS_ORIGINS=https://lead-schem.ru,https://www.lead-schem.ru`

### 4. Сборка и запуск

```bash
# Сборка образов
docker-compose -f deployment/docker-compose.production.yml build

# Запуск в фоновом режиме
docker-compose -f deployment/docker-compose.production.yml up -d

# Проверка статуса
docker-compose -f deployment/docker-compose.production.yml ps
```

### 5. Проверка работоспособности

```bash
# Проверка backend API
curl -f https://lead-schem.ru/api/v1/health

# Проверка frontend
curl -f https://lead-schem.ru

# Проверка логов
docker-compose -f deployment/docker-compose.production.yml logs -f backend
docker-compose -f deployment/docker-compose.production.yml logs -f frontend
```

### 6. Настройка мониторинга

```bash
# Проверка Prometheus
curl -f https://lead-schem.ru/prometheus

# Проверка Grafana
curl -f https://lead-schem.ru/grafana
```

---

## 🔍 Проверочный список после развертывания

### ✅ Backend API
- [ ] `/api/v1/health` возвращает 200 OK
- [ ] `/api/v1/docs` отображает Swagger UI с правильным base URL
- [ ] CORS headers содержат `lead-schem.ru` origin
- [ ] Аутентификация работает корректно

### ✅ Frontend
- [ ] Главная страница загружается по `https://lead-schem.ru`
- [ ] API запросы проходят без CORS ошибок
- [ ] Авторизация работает корректно
- [ ] Все функции приложения доступны

### ✅ База данных
- [ ] Подключение к PostgreSQL работает
- [ ] Миграции применены
- [ ] Данные загружаются корректно

### ✅ Redis
- [ ] Кеширование работает
- [ ] Сессии сохраняются

### ✅ Мониторинг
- [ ] Prometheus собирает метрики
- [ ] Grafana отображает дашборды
- [ ] Telegram уведомления работают

### ✅ SSL/Security
- [ ] HTTPS сертификаты корректны
- [ ] Редирект с HTTP на HTTPS
- [ ] Security headers установлены

---

## 🚨 Troubleshooting

### Проблема: CORS ошибки
**Решение**: Проверьте переменную `ALLOWED_ORIGINS` в .env файле

### Проблема: 502 Bad Gateway
**Решение**: Проверьте логи backend контейнера
```bash
docker-compose logs backend
```

### Проблема: База данных недоступна
**Решение**: Проверьте сетевое подключение к PostgreSQL
```bash
docker-compose exec backend python -c "from app.core.database import test_connection; test_connection()"
```

### Проблема: Redis недоступен
**Решение**: Проверьте статус Redis контейнера
```bash
docker-compose ps redis
docker-compose logs redis
```

---

## 📝 Дополнительные файлы

### Созданные файлы:
- `backend/app/core/cors_utils.py` - утилиты для динамических CORS
- `deployment/env.production.lead-schem` - продакшн конфигурация
- `scripts/fix_cors_headers.py` - скрипт для автоматического исправления CORS

### Модифицированные файлы:
- `backend/app/api/*.py` - исправлены CORS headers
- `frontend/rspack.config.cjs` - добавлены продакшн условия
- `deployment/docker-compose.production.yml` - обновлены переменные окружения
- `backend/monitoring/prometheus.yml` - исправлены Docker targets
- `backend/app/api_docs.py` - обновлены server URLs

---

## 🎯 Следующие шаги

1. **Мониторинг производительности** - настройте алерты для критических метрик
2. **Бэкапы** - настройте автоматическое резервное копирование БД
3. **CI/CD** - автоматизируйте процесс развертывания
4. **Логирование** - настройте централизованное логирование
5. **Безопасность** - проведите аудит безопасности

---

*Отчет создан: $(date)*
*Домен: lead-schem.ru*
*Статус: ✅ Готов к продакшн развертыванию* 