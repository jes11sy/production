# 🔒 РУКОВОДСТВО ПО БЕЗОПАСНОМУ DEPLOYMENT

## ⚠️ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ВЫПОЛНЕНЫ

### ✅ Исправленные проблемы безопасности:
1. **Удален файл "данные для env.txt"** с открытыми паролями
2. **Исправлены хардкод пароли** во всех docker-compose файлах
3. **Заменены хардкод секреты** на переменные окружения
4. **Исправлены скрипты создания админа** с хардкод паролями
5. **Обновлена Grafana конфигурация** без слабых паролей

## 🚀 ИНСТРУКЦИЯ ПО DEPLOYMENT

### 1. Создайте файл .env с безопасными значениями:

```bash
# Скопируйте шаблон
cp backend/config/env.production.secure .env

# Сгенерируйте безопасные пароли и ключи
openssl rand -hex 32  # для SECRET_KEY
openssl rand -hex 32  # для JWT_SECRET_KEY
openssl rand -hex 32  # для CSRF_SECRET_KEY
```

### 2. Заполните .env файл реальными данными:

```env
# === БАЗА ДАННЫХ ===
DATABASE_URL=postgresql://gen_user:ВАША_БАЗА_ПАРОЛЬ@хост:5432/база
POSTGRESQL_HOST=ваш_хост
POSTGRESQL_USER=ваш_пользователь
POSTGRESQL_PASSWORD=ваш_безопасный_пароль
POSTGRESQL_DBNAME=ваша_база
POSTGRESQL_PORT=5432

# === БЕЗОПАСНОСТЬ ===
SECRET_KEY=ваш_32_символьный_секретный_ключ
JWT_SECRET_KEY=ваш_jwt_секретный_ключ
CSRF_SECRET_KEY=ваш_csrf_секретный_ключ

# === FRONTEND ===
BACKEND_CORS_ORIGINS=["https://ваш-домен.ru","https://www.ваш-домен.ru"]

# === EMAIL ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ваш_email@gmail.com
SMTP_PASSWORD=ваш_app_пароль

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_CHAT_ID=ваш_chat_id

# === МОНИТОРИНГ ===
GRAFANA_ADMIN_PASSWORD=безопасный_пароль_grafана

# === АДМИНИСТРАТОР ===
ADMIN_PASSWORD=безопасный_пароль_админа
```

### 3. Безопасный запуск в production:

```bash
# Убедитесь что .env в .gitignore
echo ".env" >> .gitignore

# Запустите с переменными окружения
docker-compose -f deployment/docker-compose.production.yml --env-file .env up -d

# Создайте администратора
export DATABASE_URL="ваша_database_url"
export ADMIN_PASSWORD="безопасный_пароль"
python create_user_production.py
```

### 4. Проверка безопасности:

```bash
# Убедитесь что .env НЕ в репозитории
git status

# Проверьте что сервисы запустились
docker-compose -f deployment/docker-compose.production.yml ps

# Проверьте API
curl -X POST https://ваш-домен.ru/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin", "password": "ваш_админ_пароль"}'
```

## 🔐 КОНТРОЛЬНЫЙ СПИСОК БЕЗОПАСНОСТИ

### ✅ Выполнено:
- [x] Удален файл с открытыми паролями
- [x] Заменены все хардкод пароли на переменные окружения
- [x] Исправлены docker-compose файлы
- [x] Обновлены скрипты создания админа
- [x] Настроена безопасная Grafana конфигурация

### ⚠️ Требует внимания:
- [ ] Создать .env файл с безопасными значениями
- [ ] Добавить .env в .gitignore
- [ ] Сгенерировать новые секретные ключи
- [ ] Настроить SSL сертификаты
- [ ] Настроить firewall правила
- [ ] Настроить backup базы данных

## 🚨 ВАЖНЫЕ ЗАМЕЧАНИЯ

1. **НЕ КОММИТЬТЕ .env файлы** в репозиторий
2. **Сгенерируйте новые пароли** для всех сервисов
3. **Используйте HTTPS** в production
4. **Настройте мониторинг** и алерты
5. **Делайте регулярные backup** базы данных

## 📞 В случае проблем

1. Проверьте логи: `docker-compose logs -f`
2. Проверьте переменные окружения
3. Убедитесь что .env файл корректно загружен
4. Проверьте сетевую доступность сервисов 