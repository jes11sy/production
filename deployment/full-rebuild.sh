#!/bin/bash

echo "🚀 ПОЛНАЯ ПЕРЕСБОРКА LEADSCHEM CRM С ОЧИСТКОЙ КЕША"
echo "=================================================="

# Остановить все сервисы
echo "⏹️  Остановка всех сервисов..."
docker-compose -f docker-compose.production.yml down

# ПОЛНАЯ ОЧИСТКА КЕША
echo "🧹 Очистка всего Docker кеша..."

# Удалить все контейнеры
echo "  - Удаление всех контейнеров..."
docker container prune -f

# Удалить все образы leadschem
echo "  - Удаление образов leadschem..."
docker images | grep leadschem | awk '{print $3}' | xargs -r docker rmi -f

# Удалить build кеш
echo "  - Очистка build кеша..."
docker builder prune -af

# Удалить system кеш
echo "  - Очистка system кеша..."
docker system prune -af

# Удалить volumes (ОСТОРОЖНО - потеряются данные)
echo "  - Очистка volumes..."
docker volume prune -f

# Удалить networks
echo "  - Очистка networks..."
docker network prune -f

# Показать освобожденное место
echo "💾 Состояние Docker после очистки:"
docker system df

# Обновить код с GitHub
echo "📥 Обновление кода с GitHub..."
git stash
git pull origin main
git stash pop

# Пересборка образов БЕЗ КЕША
echo "🔨 Пересборка образов без кеша..."
docker-compose -f docker-compose.production.yml build --no-cache --pull

# Запуск сервисов
echo "🚀 Запуск обновленных сервисов..."
docker-compose -f docker-compose.production.yml up -d

# Проверка статуса
echo "📊 Проверка статуса сервисов..."
sleep 10
docker-compose -f docker-compose.production.yml ps

echo ""
echo "✅ ПЕРЕСБОРКА ЗАВЕРШЕНА!"
echo "🌐 Проверьте доступность:"
echo "   - HTTP:  http://your-server-ip/"
echo "   - HTTPS: https://lead-schem.ru/"
echo "   - API:   https://lead-schem.ru/docs"
echo ""
echo "📋 Мониторинг логов:"
echo "   docker-compose -f docker-compose.production.yml logs -f" 