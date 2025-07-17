# 🚀 Обновление сервера production

## Способ 1: Автоматический (рекомендуется)

### Скачать и запустить скрипт обновления:

```bash
# Подключение к серверу
ssh root@lead-schem.ru

# Скачивание скрипта обновления
cd /opt/leadschem
wget https://raw.githubusercontent.com/jes11sy/production/main/deployment/update-server.sh
chmod +x update-server.sh

# Запуск обновления
./update-server.sh
```

## Способ 2: Ручное обновление

### Пошаговые команды:

```bash
# 1. Подключение к серверу
ssh root@lead-schem.ru

# 2. Переход в рабочую директорию
cd /opt/leadschem

# 3. Проверка текущего состояния
git status
git log --oneline -3

# 4. Сохранение локальных изменений (если есть)
git stash

# 5. Получение последних изменений
git fetch origin

# 6. Обновление кода
git reset --hard origin/main

# 7. Проверка CORS настроек
if ! grep -q "ALLOWED_ORIGINS" .env; then
    echo "" >> .env
    echo "# CORS settings" >> .env
    echo "ALLOWED_ORIGINS=https://lead-schem.ru,https://www.lead-schem.ru" >> .env
    echo "CORS_CREDENTIALS=true" >> .env
fi

# 8. Перезапуск сервисов
docker-compose -f deployment/docker-compose.production.yml down
docker-compose -f deployment/docker-compose.production.yml build --no-cache
docker-compose -f deployment/docker-compose.production.yml up -d

# 9. Проверка статуса
sleep 15
docker-compose -f deployment/docker-compose.production.yml ps
```

## Способ 3: Быстрое обновление (только код)

Если нужно обновить только код без полной пересборки:

```bash
ssh root@lead-schem.ru
cd /opt/leadschem
git pull origin main
docker-compose -f deployment/docker-compose.production.yml restart backend frontend
```

## Проверка успешного обновления

### 1. Проверка git коммита:
```bash
git log --oneline -1
# Должен показать: 0fef08e CORS исправление для production
```

### 2. Проверка сервисов:
```bash
docker-compose -f deployment/docker-compose.production.yml ps
# Все сервисы должны быть Up
```

### 3. Проверка CORS:
```bash
curl -X OPTIONS "https://lead-schem.ru/api/v1/auth/login" \
  -H "Origin: https://lead-schem.ru" \
  -H "Access-Control-Request-Method: POST" \
  -I | grep "access-control-allow-origin"
```
Должен вернуть: `access-control-allow-origin: https://lead-schem.ru`

### 4. Проверка API:
```bash
curl "https://lead-schem.ru/api/v1/health"
# Должен вернуть: {"status": "ok", ...}
```

### 5. Проверка сайта:
Откройте https://lead-schem.ru в браузере - должен работать полноценно.

## Устранение проблем

### Если сервисы не запускаются:
```bash
# Проверка логов
docker-compose -f deployment/docker-compose.production.yml logs

# Принудительная пересборка
docker-compose -f deployment/docker-compose.production.yml down
docker system prune -f
docker-compose -f deployment/docker-compose.production.yml up -d --build
```

### Если CORS не работает:
```bash
# Проверка переменных
grep CORS /opt/leadschem/.env

# Добавление вручную
echo "ALLOWED_ORIGINS=https://lead-schem.ru,https://www.lead-schem.ru" >> .env
docker-compose -f deployment/docker-compose.production.yml restart backend
```

## Что будет обновлено

1. ✅ **Backend код** с исправлениями CORS
2. ✅ **Frontend код** (если есть изменения)
3. ✅ **Docker образы** пересобираются
4. ✅ **CORS настройки** добавляются автоматически
5. ✅ **Все сервисы** перезапускаются

## Время выполнения

- **Автоматический способ**: ~3-5 минут
- **Ручное обновление**: ~5-10 минут
- **Быстрое обновление**: ~1-2 минуты

---

**Рекомендация**: Используйте автоматический способ для безопасного обновления. 