# 🚀 Развертывание Lead Schema на Production

Полное руководство по развертыванию проекта **Lead Schema** на production сервере.

## 📋 Информация о сервере

- **IP:** 194.87.201.221
- **Домен:** lead-schem.ru
- **OS:** Ubuntu 20.04/22.04
- **Доступ:** root:r#5zajF#.V1K79

## 📋 Существующая база данных

- **Хост:** 74ac89b6f8cc981b84f28f3b.twc1.net:5432
- **База:** default_db
- **Пользователь:** gen_user
- **Пароль:** [ИСПОЛЬЗОВАТЬ ИЗ ВАШЕГО .env ФАЙЛА]

## 🎯 Архитектура развертывания

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Frontend      │    │   Backend API   │
│   (SSL/HTTPS)   │───▶│   (React/Vite)  │───▶│   (FastAPI)     │
│   Port 80/443   │    │   Port 3000     │    │   Port 8000     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │     Redis       │    │   PostgreSQL    │
         │              │   (Cache)       │    │ (Внешняя БД)    │
         │              │   Port 6379     │    │   Port 5432     │
         │              └─────────────────┘    └─────────────────┘
         │
   ┌─────────────────┐    ┌─────────────────┐
   │   Grafana       │    │   Prometheus    │
   │  (Мониторинг)   │    │   (Метрики)     │
   │   Port 3001     │    │   Port 9090     │
   └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрое развертывание

### Шаг 1: Подключение к серверу

```bash
ssh root@194.87.201.221
# Пароль: r#5zajF#.V1K79
```

### Шаг 2: Загрузка проекта

```bash
# Создать временную папку и загрузить проект
mkdir -p /tmp/leadschem
cd /tmp/leadschem

# Загрузить архив проекта или склонировать репозиторий
# scp -r local_project/* root@194.87.201.221:/tmp/leadschem/
```

### Шаг 3: Запуск автоматической установки

```bash
cd /tmp/leadschem/deployment
chmod +x deploy.sh
./deploy.sh
# Выбрать: 1) Полная установка (новый сервер)
```

## 📋 Пошаговое развертывание

### 1️⃣ Подготовка сервера

```bash
# Запуск скрипта установки базовых компонентов
chmod +x server-setup.sh
./server-setup.sh
```

**Что устанавливается:**
- Docker и Docker Compose
- Nginx
- Node.js
- PostgreSQL клиент
- Certbot (Let's Encrypt)
- Система безопасности (UFW, fail2ban)

### 2️⃣ Настройка проекта

```bash
# Копирование проекта в production директорию
cp -r /tmp/leadschem/* /opt/leadschem/
chown -R leadschem:leadschem /opt/leadschem
cd /opt/leadschem
```

### 3️⃣ Настройка переменных окружения

```bash
# Копирование и редактирование env файла
cp deployment/env.production.example .env
nano .env

# Основные настройки для изменения:
# - SECRET_KEY (сгенерировать новый)
# - EMAIL_HOST_USER/EMAIL_HOST_PASSWORD
# - GRAFANA_ADMIN_PASSWORD
```

### 4️⃣ Сборка и запуск приложения

```bash
cd /opt/leadschem/deployment
docker-compose -f docker-compose.production.yml up -d
```

### 5️⃣ Настройка SSL

```bash
# Настройка Let's Encrypt сертификатов
chmod +x setup-ssl.sh
./setup-ssl.sh
```

### 6️⃣ Настройка Nginx

```bash
# Копирование конфигурации Nginx
cp nginx/lead-schem.ru.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/lead-schem.ru /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## 🔍 Проверка развертывания

### Проверка сервисов

```bash
# Статус Docker контейнеров
docker ps

# Статус системных сервисов
systemctl status nginx
systemctl status leadschem

# Использование встроенного скрипта проверки
./deploy.sh
# Выбрать: 6) Проверка статуса
```

### Проверка доступности

- **Frontend:** https://lead-schem.ru
- **Backend API:** https://lead-schem.ru/api/v1/docs
- **Мониторинг:** https://lead-schem.ru/monitoring
- **Метрики:** https://lead-schem.ru/metrics (только с разрешенных IP)

### Проверка логов

```bash
# Просмотр логов через скрипт
./deploy.sh
# Выбрать: 7) Просмотр логов

# Или напрямую:
docker logs leadschem_backend
docker logs leadschem_frontend
tail -f /var/log/nginx/lead-schem.ru.access.log
```

## 🔧 Управление приложением

### Основные команды

```bash
# Запуск приложения
systemctl start leadschem

# Остановка приложения
systemctl stop leadschem

# Перезапуск приложения
systemctl restart leadschem

# Статус приложения
systemctl status leadschem

# Перезапуск через Docker Compose
cd /opt/leadschem/deployment
docker-compose -f docker-compose.production.yml restart
```

### Обновление приложения

```bash
cd /opt/leadschem/deployment
./deploy.sh
# Выбрать: 3) Обновление приложения
```

### Резервное копирование

```bash
# Создание backup базы данных
./deploy.sh
# Выбрать: 8) Backup базы данных

# Backup создается в /opt/leadschem/backups/
```

## 📊 Мониторинг

### Grafana

- **URL:** https://lead-schem.ru/monitoring
- **Логин:** admin
- **Пароль:** LeAdScHeM_GrAfAnA_2025 (измените в .env)

### Prometheus

- **URL:** http://194.87.201.221:9090 (внутренний доступ)
- Метрики приложения автоматически собираются

### Проверка SSL

```bash
# Информация о сертификате
check-ssl

# Тест обновления сертификата
certbot renew --dry-run
```

## 🛡️ Безопасность

### Настроенная защита

- **UFW брандмауэр** с ограниченными портами
- **fail2ban** для защиты от брутфорс атак
- **SSL/TLS** с современными настройками
- **HSTS** заголовки
- **CSP** политики
- **Rate limiting** на API

### Рекомендуемые действия

1. **Измените пароли по умолчанию:**
   ```bash
   nano /opt/leadschem/.env
   # Измените: SECRET_KEY, GRAFANA_ADMIN_PASSWORD
   ```

2. **Настройте email уведомления:**
   ```bash
   nano /opt/leadschem/.env
   # Настройте: EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
   ```

3. **Настройте регулярные backup:**
   ```bash
   crontab -e
   # Добавьте: 0 2 * * * /opt/leadschem/deployment/deploy.sh backup
   ```

## 🐛 Устранение неполадок

### Частые проблемы

1. **Сайт недоступен:**
   ```bash
   # Проверить статус Nginx
   systemctl status nginx
   
   # Проверить конфигурацию
   nginx -t
   
   # Проверить логи
   tail -f /var/log/nginx/error.log
   ```

2. **API не отвечает:**
   ```bash
   # Проверить backend контейнер
   docker logs leadschem_backend
   
   # Перезапустить backend
   docker restart leadschem_backend
   ```

3. **База данных недоступна:**
   ```bash
   # Проверить подключение к внешней БД
   PGPASSWORD="Jple\$?}bl!hCd3" psql -h 74ac89b6f8cc981b84f28f3b.twc1.net -U gen_user -d default_db -c "SELECT 1;"
   ```

4. **SSL проблемы:**
   ```bash
   # Обновить сертификат
   certbot renew
   
   # Перезапустить Nginx
   systemctl reload nginx
   ```

### Логи и диагностика

```bash
# Системные логи
journalctl -u nginx
journalctl -u leadschem

# Docker логи
docker logs leadschem_backend --tail=100
docker logs leadschem_frontend --tail=100

# Логи приложения
tail -f /opt/leadschem/logs/app.log
```

## 📞 Поддержка

### Полезные команды

```bash
# Быстрая диагностика
./deploy.sh  # и выберите нужное действие

# Проверка SSL
check-ssl

# Монитор ресурсов
htop
df -h
free -h
```

### Контакты и документация

- **Проект:** /opt/leadschem
- **Логи:** /opt/leadschem/logs/
- **Конфигурация:** /opt/leadschem/.env
- **Backup:** /opt/leadschem/backups/

---

## ✅ Чек-лист развертывания

- [ ] Сервер настроен (Docker, Nginx, etc.)
- [ ] Проект скопирован в /opt/leadschem
- [ ] Переменные окружения настроены
- [ ] Docker контейнеры запущены
- [ ] SSL сертификат получен
- [ ] Nginx настроен
- [ ] Домен lead-schem.ru доступен
- [ ] API доступно на /api/v1/docs
- [ ] Мониторинг настроен
- [ ] Backup настроен
- [ ] Пароли изменены
- [ ] Email уведомления настроены

**🎉 Проект успешно развернут на https://lead-schem.ru!** 