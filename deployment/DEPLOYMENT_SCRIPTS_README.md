# 🚀 СКРИПТЫ АВТОМАТИЧЕСКОГО РАЗВЕРТЫВАНИЯ

Набор скриптов для автоматического развертывания и управления production сервером Lead Schema.

## 📋 Содержание

- [🏗️ auto-deploy.sh](#-auto-deploysh) - Полное автоматическое развертывание
- [👤 create-admin.sh](#-create-adminsh) - Создание админ пользователя  
- [🔄 update-app.sh](#-update-appsh) - Обновление приложения
- [📊 monitor-system.sh](#-monitor-systemsh) - Мониторинг системы

---

## 🏗️ auto-deploy.sh

**Назначение:** Полное автоматическое развертывание системы с нуля.

### Что делает:
1. ✅ Устанавливает системные зависимости (Docker, Nginx, etc.)
2. ✅ Настраивает firewall и безопасность
3. ✅ Клонирует репозиторий и настраивает проект
4. ✅ Создает .env файл с автогенерированными ключами
5. ✅ Настраивает SSL сертификаты (Let's Encrypt)
6. ✅ Разворачивает Docker контейнеры
7. ✅ Настраивает мониторинг (Prometheus + Grafana)
8. ✅ Проверяет работоспособность всех компонентов

### Использование:

```bash
# ВАЖНО: Перед запуском измените REPO_URL в скрипте!
sudo nano /path/to/auto-deploy.sh  # Строка 29: замените на ваш репозиторий

# Полное развертывание
sudo ./auto-deploy.sh

# Пропустить установку зависимостей
sudo ./auto-deploy.sh --skip-deps

# Без SSL (для тестирования)  
sudo ./auto-deploy.sh --no-ssl

# Показать справку
./auto-deploy.sh --help
```

### ⚠️ ВАЖНО:
1. **Измените REPO_URL** на адрес вашего репозитория
2. **Запускайте только от root** (sudo)
3. **Скрипт остановится** для редактирования .env файла
4. **Укажите реальные данные БД** в .env перед продолжением

---

## 👤 create-admin.sh

**Назначение:** Создание администратора после развертывания.

### Что делает:
- ✅ Проверяет работу backend контейнера
- ✅ Создает пользователя с ролью admin
- ✅ Хеширует пароль безопасным способом
- ✅ Проверяет уникальность логина

### Использование:

```bash
# Запуск на production сервере
cd /opt/leadschem
sudo ./deployment/create-admin.sh
```

Скрипт запросит:
- 📝 Логин админа
- 🔐 Пароль (минимум 8 символов)
- 📧 Email
- 👤 Имя

### Пример:
```
📝 Введите логин админа: admin
🔐 Введите пароль админа: ********
📧 Введите email админа: admin@lead-schem.ru
👤 Введите имя админа: Администратор
```

---

## 🔄 update-app.sh

**Назначение:** Безопасное обновление приложения без простоев.

### Что делает:
1. ✅ Создает backup базы данных и конфигураций
2. ✅ Обновляет код из Git репозитория
3. ✅ Пересобирает контейнеры при необходимости
4. ✅ Выполняет rolling update (без простоев)
5. ✅ Применяет миграции БД
6. ✅ Проверяет работоспособность
7. ✅ Откатывается при ошибках

### Использование:

```bash
cd /opt/leadschem

# Полное обновление с backup
sudo ./deployment/update-app.sh

# Быстрое обновление без backup
sudo ./deployment/update-app.sh --quick

# Только миграции БД
sudo ./deployment/update-app.sh --migrations-only

# Полное обновление без backup
sudo ./deployment/update-app.sh --no-backup

# Показать справку
./deployment/update-app.sh --help
```

### Особенности:
- 🔄 **Rolling update** - сначала backend, потом frontend
- 💾 **Автоматический backup** перед обновлением
- 🔙 **Автоматический откат** при ошибках
- ⚡ **Умная пересборка** - только при изменении зависимостей

---

## 📊 monitor-system.sh

**Назначение:** Комплексный мониторинг состояния production системы.

### Что проверяет:
- 💻 **Системные ресурсы** (CPU, память, диск)
- 🐳 **Docker контейнеры** (статус, ресурсы)
- 🌐 **Сетевые сервисы** (API, сайт, БД)
- 🔒 **Nginx и SSL** (конфигурация, сертификаты)
- 📝 **Логи** (ошибки за последний час)
- 🗄️ **База данных** (размер, подключения)
- 💾 **Backup** (последние копии)

### Использование:

```bash
cd /opt/leadschem

# Полная диагностика всех компонентов
./deployment/monitor-system.sh

# Быстрая проверка основных сервисов
./deployment/monitor-system.sh --quick

# Только системные ресурсы
./deployment/monitor-system.sh --system

# Только Docker контейнеры
./deployment/monitor-system.sh --docker

# Только сетевые сервисы
./deployment/monitor-system.sh --network

# Только Nginx и SSL
./deployment/monitor-system.sh --nginx

# Только анализ логов
./deployment/monitor-system.sh --logs

# Только база данных
./deployment/monitor-system.sh --database

# Только backup файлы
./deployment/monitor-system.sh --backup

# Показать справку
./deployment/monitor-system.sh --help
```

### Пример вывода:
```
╔══════════════════════════════════════════════════════════════╗
║               📊 МОНИТОРИНГ LEAD-SCHEM                      ║
║                    Mon Jan 15 21:30:00 UTC 2025             ║
╚══════════════════════════════════════════════════════════════╝

=== 💻 СИСТЕМНЫЕ РЕСУРСЫ ===
[OK] CPU загрузка: 15.2%
[OK] Load Average: 0.45
[OK] Память: 2.1G/8.0G (26.3%)

=== 🐳 DOCKER КОНТЕЙНЕРЫ ===
[OK] leadschem_backend: Up 2 hours
[OK] leadschem_frontend: Up 2 hours
[OK] leadschem_redis: Up 2 hours

=== 📋 СВОДКА СОСТОЯНИЯ ===
[OK] Общее состояние: ВСЕ СЕРВИСЫ РАБОТАЮТ НОРМАЛЬНО ✅
```

---

## 🛠️ Установка и настройка

### 1. Подготовка скриптов

```bash
# Скачайте скрипты на сервер
scp deployment/*.sh root@your-server:/root/

# Или клонируйте репозиторий
git clone your-repo-url /opt/leadschem

# Дайте права на выполнение
chmod +x /opt/leadschem/deployment/*.sh
```

### 2. Первоначальное развертывание

```bash
# 1. Отредактируйте auto-deploy.sh
nano /opt/leadschem/deployment/auto-deploy.sh
# Измените REPO_URL на адрес вашего репозитория (строка 29)

# 2. Запустите автоматическое развертывание
cd /opt/leadschem
sudo ./deployment/auto-deploy.sh

# 3. Скрипт остановится для редактирования .env
# Укажите реальные данные подключения к БД:
nano /opt/leadschem/.env
# Замените YOUR_USER, YOUR_PASSWORD, etc. на реальные значения

# 4. Продолжите развертывание
sudo ./deployment/auto-deploy.sh

# 5. Создайте админ пользователя
sudo ./deployment/create-admin.sh
```

### 3. Регулярное использование

```bash
# Обновление приложения
sudo /opt/leadschem/deployment/update-app.sh

# Мониторинг системы
/opt/leadschem/deployment/monitor-system.sh --quick

# Создание дополнительных пользователей
sudo /opt/leadschem/deployment/create-admin.sh
```

---

## 📅 Автоматизация

### Cron задачи для мониторинга

```bash
# Добавить в crontab (sudo crontab -e)

# Ежедневный мониторинг в 9:00
0 9 * * * /opt/leadschem/deployment/monitor-system.sh --quick >> /var/log/leadschem-monitor.log 2>&1

# Еженедельная полная диагностика в воскресенье 6:00  
0 6 * * 0 /opt/leadschem/deployment/monitor-system.sh >> /var/log/leadschem-full-check.log 2>&1
```

---

## 🔧 Устранение неполадок

### Основные проблемы:

**❌ "Permission denied"**
```bash
sudo chmod +x /opt/leadschem/deployment/*.sh
```

**❌ "Docker not found"**
```bash
sudo ./deployment/auto-deploy.sh --skip-deps  # Установить Docker вручную
```

**❌ "Backend недоступен"**
```bash
# Проверить логи
docker compose -f /opt/leadschem/deployment/docker-compose.production.yml logs backend

# Перезапустить контейнер
docker compose -f /opt/leadschem/deployment/docker-compose.production.yml restart backend
```

**❌ "SSL сертификат не найден"**
```bash
# Получить сертификат вручную
sudo certbot certonly --webroot -w /var/www/html -d lead-schem.ru -d www.lead-schem.ru
```

### Логи и диагностика:

```bash
# Логи всех контейнеров
docker compose -f /opt/leadschem/deployment/docker-compose.production.yml logs -f

# Логи конкретного сервиса
docker compose -f /opt/leadschem/deployment/docker-compose.production.yml logs -f backend

# Статус всех сервисов
docker compose -f /opt/leadschem/deployment/docker-compose.production.yml ps

# Системные логи
journalctl -u nginx -f
tail -f /var/log/nginx/error.log
```

---

## 📞 Поддержка

Если возникли проблемы:

1. **Проверьте логи** с помощью команд выше
2. **Запустите диагностику:** `./deployment/monitor-system.sh`
3. **Проверьте .env файл** на корректность данных
4. **Убедитесь в доступности БД** и внешних сервисов

---

## ✅ Чек-лист готовности к production

- [ ] Изменен REPO_URL в auto-deploy.sh
- [ ] Настроен .env файл с реальными данными БД
- [ ] Получены SSL сертификаты
- [ ] Создан админ пользователь
- [ ] Настроен мониторинг и алерты
- [ ] Проверена работа backup
- [ ] Настроены cron задачи для мониторинга

🎉 **Проект готов к production использованию!** 