#!/bin/bash

# Скрипт для обновления кода на production сервере
# Запускать на сервере под root

set -e

echo "🚀 Обновление кода на production сервере..."

# Переходим в рабочую директорию
cd /opt/leadschem

# Проверяем текущую ветку
echo "📋 Текущая ветка:"
git branch

# Проверяем статус
echo "📋 Статус git:"
git status

# Сохраняем локальные изменения если есть
if ! git diff --quiet; then
    echo "💾 Сохраняем локальные изменения..."
    git stash push -m "Auto-stash before update $(date)"
fi

# Получаем последние изменения
echo "📥 Получение последних изменений..."
git fetch origin

# Обновляем до последней версии
echo "🔄 Обновление до последней версии main..."
git reset --hard origin/main

# Показываем последние коммиты
echo "📜 Последние коммиты:"
git log --oneline -5

# Добавляем CORS переменные если их нет
echo "🔧 Проверка CORS настроек..."
if ! grep -q "ALLOWED_ORIGINS" .env; then
    echo "" >> .env
    echo "# CORS settings" >> .env
    echo "ALLOWED_ORIGINS=https://lead-schem.ru,https://www.lead-schem.ru" >> .env
    echo "CORS_CREDENTIALS=true" >> .env
    echo "✅ CORS переменные добавлены"
else
    echo "ℹ️  CORS переменные уже существуют"
fi

# Перезапуск сервисов
echo "🔄 Перезапуск сервисов..."

# Останавливаем все сервисы
docker-compose -f deployment/docker-compose.production.yml down

# Пересобираем образы (если изменился код)
docker-compose -f deployment/docker-compose.production.yml build --no-cache

# Запускаем все сервисы
docker-compose -f deployment/docker-compose.production.yml up -d

echo "⏱️  Ожидание запуска сервисов..."
sleep 15

# Проверка статуса
echo "🔍 Проверка статуса сервисов..."
docker-compose -f deployment/docker-compose.production.yml ps

# Проверка логов backend
echo "📋 Последние логи backend:"
docker-compose -f deployment/docker-compose.production.yml logs --tail=20 backend

# Проверка CORS
echo "🌐 Проверка CORS..."
curl -s -X OPTIONS "https://lead-schem.ru/api/v1/auth/login" \
  -H "Origin: https://lead-schem.ru" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -I | grep -i "access-control" || echo "CORS заголовки не найдены"

echo "✅ Обновление завершено!"
echo ""
echo "🔗 Проверьте сайт: https://lead-schem.ru"
echo "🔗 API здоровье: https://lead-schem.ru/api/v1/health" 