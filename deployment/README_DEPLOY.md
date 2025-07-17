# 🚀 Руководство по развертыванию LeadSchem Production

Это полное руководство по развертыванию системы управления лидами LeadSchem в продакшн среде.

## 📋 Содержание

- [Системные требования](#системные-требования)
- [Быстрый старт](#быстрый-старт)
- [Детальная настройка](#детальная-настройка)
- [Управление системой](#управление-системой)
- [Мониторинг](#мониторинг)
- [Безопасность](#безопасность)
- [Решение проблем](#решение-проблем)

## 🔧 Системные требования

### Минимальные требования
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 4GB (рекомендуется 8GB+)
- **CPU**: 2 ядра (рекомендуется 4+)
- **Диск**: 20GB свободного места (рекомендуется 50GB+)
- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+

### Порты
Система использует следующие порты:
- `80` - HTTP (редирект на HTTPS)
- `443` - HTTPS (фронтенд и API)
- `3000` - Frontend (внутренний)
- `8000` - Backend API (внутренний)
- `6379` - Redis (внутренний)
- `9090` - Prometheus (внутренний)
- `3001` - Grafana (внутренний)

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/jes11sy/production.git
cd production/deployment
```

### 2. Запуск автоматического деплоя
```bash
chmod +x full-deploy.sh
./full-deploy.sh
```

Скрипт автоматически:
- ✅ Проверит системные требования
- ✅ Создаст файл конфигурации
- ✅ Настроит все сервисы
- ✅ Запустит приложение
- ✅ Создаст администратора
- ✅ Проверит работоспособность

### 3. Первый вход
После успешного деплоя:
- **Фронтенд**: http://localhost:3000
- **Логин**: admin
- **Пароль**: admin123 ⚠️ ОБЯЗАТЕЛЬНО СМЕНИТЕ!

## ⚙️ Детальная настройка

### Конфигурация окружения

Отредактируйте файл `env.production.lead-schem`:

```bash
# КРИТИЧЕСКИ ВАЖНО ИЗМЕНИТЬ ЭТИ ЗНАЧЕНИЯ:

# База данных
POSTGRESQL_PASSWORD=your_very_strong_password_here

# Безопасность
SECRET_KEY=your_super_long_secret_key_minimum_32_characters
JWT_SECRET_KEY=another_super_long_secret_key_for_jwt

# Email (для уведомлений)
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Grafana
GRAFANA_ADMIN_PASSWORD=strong_grafana_password
```

### SSL сертификаты (для продакшена)

```bash
# Установка Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Получение сертификатов
sudo certbot --nginx -d lead-schem.ru -d www.lead-schem.ru

# Автопродление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🎛️ Управление системой

### Основные команды

```bash
# Переход в папку деплоя
cd deployment/

# Просмотр статуса
docker-compose -f docker-compose.production.yml ps

# Просмотр логов
docker-compose -f docker-compose.production.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.production.yml logs -f backend

# Перезапуск сервиса
docker-compose -f docker-compose.production.yml restart backend

# Остановка всех сервисов
docker-compose -f docker-compose.production.yml down

# Полная остановка с удалением volumes
docker-compose -f docker-compose.production.yml down -v
```

### Обновление системы

```bash
# 1. Остановка системы
docker-compose -f docker-compose.production.yml down

# 2. Обновление кода
git pull origin main

# 3. Пересборка образов
docker-compose -f docker-compose.production.yml build --no-cache

# 4. Запуск
docker-compose -f docker-compose.production.yml --env-file env.production.lead-schem up -d

# 5. Миграции БД (если нужно)
docker-compose -f docker-compose.production.yml exec backend python -m alembic upgrade head
```

## 📊 Мониторинг

### Доступные интерфейсы
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **API Health**: http://localhost:8000/health
- **API Metrics**: http://localhost:8000/metrics

### Основные метрики
- Время ответа API
- Количество запросов
- Использование ресурсов
- Статус базы данных
- Статус Redis

### Алерты
Система автоматически мониторит:
- Доступность сервисов
- Ошибки в логах
- Использование ресурсов
- Время ответа

## 🔒 Безопасность

### Обязательные действия после деплоя

1. **Смена паролей**:
   ```bash
   # Вход в систему и смена пароля администратора
   # Frontend -> Настройки -> Смена пароля
   ```

2. **Настройка файрвола**:
   ```bash
   sudo ufw enable
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 22/tcp
   sudo ufw reload
   ```

3. **Регулярные обновления**:
   ```bash
   # Еженедельно
   sudo apt update && sudo apt upgrade -y
   docker system prune -f
   ```

### Резервное копирование

```bash
# Создание бэкапа
./backup.sh

# Восстановление
./restore.sh backup_20241201_120000
```

## 🐛 Решение проблем

### Часто встречающиеся проблемы

#### 1. Порты заняты
```bash
# Проверка занятых портов
sudo netstat -tuln | grep :8000

# Остановка конфликтующих процессов
sudo fuser -k 8000/tcp
```

#### 2. Проблемы с Docker
```bash
# Очистка Docker
docker system prune -a -f
docker volume prune -f

# Перезапуск Docker
sudo systemctl restart docker
```

#### 3. Ошибки базы данных
```bash
# Проверка логов PostgreSQL
docker-compose -f docker-compose.production.yml logs postgres

# Подключение к БД
docker-compose -f docker-compose.production.yml exec postgres psql -U leadschem_user -d leadschem_db
```

#### 4. Проблемы с SSL
```bash
# Проверка сертификатов
sudo certbot certificates

# Тест конфигурации Nginx
sudo nginx -t

# Обновление сертификатов
sudo certbot renew --dry-run
```

### Диагностика

```bash
# Проверка всех сервисов
./health-check.sh

# Детальные логи
docker-compose -f docker-compose.production.yml logs --tail=100

# Проверка ресурсов
docker stats
```

## 📞 Поддержка

### Логи и диагностика
Все логи сохраняются в:
- `../logs/` - логи приложения
- `docker-compose logs` - логи контейнеров

### Контакты
- **Техподдержка**: admin@lead-schem.ru
- **Документация**: https://github.com/jes11sy/production/docs
- **Issues**: https://github.com/jes11sy/production/issues

---

## 📝 Дополнительная информация

### Архитектура системы
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Nginx    │───▶│   Frontend  │───▶│   Backend   │
│   (Proxy)   │    │   (React)   │    │  (FastAPI)  │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                   ┌─────────────┐          │
                   │    Redis    │◄─────────┤
                   │   (Cache)   │          │
                   └─────────────┘          │
                                            │
                   ┌─────────────┐          │
                   │ PostgreSQL  │◄─────────┘
                   │ (Database)  │
                   └─────────────┘
```

### Мониторинг
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Application │───▶│ Prometheus  │───▶│   Grafana   │
│  (Metrics)  │    │ (Collector) │    │ (Dashboard) │
└─────────────┘    └─────────────┘    └─────────────┘
```

---
*Последнее обновление: декабрь 2024* 