#!/bin/bash

# =========================================
# 🔄 БЫСТРОЕ ОБНОВЛЕНИЕ ПРИЛОЖЕНИЯ
# =========================================

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

PROJECT_DIR="/opt/leadschem"
BACKUP_DIR="/opt/leadschem/backups"

# Проверка что мы на production сервере
if [ ! -d "$PROJECT_DIR" ]; then
    error "❌ Директория проекта $PROJECT_DIR не найдена"
fi

cd $PROJECT_DIR

log "🔄 Начинаем обновление приложения..."

# =========================================
# 1. ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА
# =========================================

pre_update_check() {
    log "🔍 Предварительная проверка..."
    
    # Проверка что контейнеры запущены
    if ! docker compose -f deployment/docker-compose.production.yml ps | grep -q "Up"; then
        error "❌ Контейнеры не запущены. Запустите их сначала."
    fi
    
    # Проверка доступности сайта
    if ! curl -s -f https://lead-schem.ru/health > /dev/null; then
        warn "⚠️  Сайт недоступен, но продолжаем обновление"
    fi
    
    # Проверка свободного места
    AVAILABLE_SPACE=$(df /opt | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_SPACE" -lt 1048576 ]; then  # Меньше 1GB
        warn "⚠️  Мало свободного места на диске (< 1GB)"
    fi
    
    log "✅ Предварительная проверка завершена"
}

# =========================================
# 2. СОЗДАНИЕ BACKUP
# =========================================

create_backup() {
    log "💾 Создание backup перед обновлением..."
    
    mkdir -p $BACKUP_DIR
    
    # Backup базы данных
    source $PROJECT_DIR/.env
    
    BACKUP_FILE="$BACKUP_DIR/pre_update_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log "🗄️ Создание backup базы данных..."
    PGPASSWORD="$POSTGRESQL_PASSWORD" pg_dump \
        -h "$POSTGRESQL_HOST" \
        -U "$POSTGRESQL_USER" \
        -d "$POSTGRESQL_DBNAME" \
        -f "$BACKUP_FILE"
    
    gzip "$BACKUP_FILE"
    log "✅ Backup БД создан: ${BACKUP_FILE}.gz"
    
    # Backup media файлов
    log "📁 Создание backup media файлов..."
    tar -czf "$BACKUP_DIR/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz" -C /opt/leadschem media/ || warn "⚠️  Ошибка backup media файлов"
    
    # Backup конфигураций
    log "⚙️ Создание backup конфигураций..."
    cp $PROJECT_DIR/.env "$BACKUP_DIR/env_backup_$(date +%Y%m%d_%H%M%S)"
    
    log "✅ Backup завершен"
}

# =========================================
# 3. ОБНОВЛЕНИЕ КОДА
# =========================================

update_code() {
    log "📥 Обновление кода из репозитория..."
    
    # Сохранение текущего коммита
    CURRENT_COMMIT=$(git rev-parse HEAD)
    echo $CURRENT_COMMIT > "$BACKUP_DIR/last_commit_$(date +%Y%m%d_%H%M%S)"
    
    # Обновление кода
    git fetch origin
    git pull origin main
    
    NEW_COMMIT=$(git rev-parse HEAD)
    
    if [ "$CURRENT_COMMIT" == "$NEW_COMMIT" ]; then
        log "ℹ️  Код уже актуален"
    else
        log "✅ Код обновлен с $CURRENT_COMMIT на $NEW_COMMIT"
    fi
}

# =========================================
# 4. ОБНОВЛЕНИЕ КОНТЕЙНЕРОВ
# =========================================

update_containers() {
    log "🐳 Обновление Docker контейнеров..."
    
    # Пересборка только если есть изменения в Dockerfile
    if git diff --name-only HEAD~1 HEAD | grep -E "(Dockerfile|requirements\.txt|package\.json)"; then
        log "🔨 Обнаружены изменения в зависимостях, пересобираем контейнеры..."
        docker compose -f deployment/docker-compose.production.yml build --no-cache
    else
        log "ℹ️  Изменений в зависимостях нет, используем существующие образы"
    fi
    
    # Обновление и перезапуск сервисов
    log "🔄 Перезапуск сервисов..."
    
    # Rolling update - сначала backend, потом frontend
    docker compose -f deployment/docker-compose.production.yml up -d --no-deps backend
    
    # Ждем пока backend поднимется
    log "⏳ Ожидание запуска backend..."
    sleep 15
    
    # Проверка backend
    for i in {1..12}; do
        if curl -s -f http://127.0.0.1:8000/health > /dev/null; then
            log "✅ Backend запущен"
            break
        fi
        if [ $i -eq 12 ]; then
            error "❌ Backend не запустился в течение 60 секунд"
        fi
        sleep 5
    done
    
    # Теперь обновляем frontend
    docker compose -f deployment/docker-compose.production.yml up -d --no-deps frontend
    
    # Ждем frontend
    log "⏳ Ожидание запуска frontend..."
    sleep 10
    
    log "✅ Контейнеры обновлены"
}

# =========================================
# 5. ВЫПОЛНЕНИЕ МИГРАЦИЙ
# =========================================

run_migrations() {
    log "🔧 Выполнение миграций базы данных..."
    
    # Проверка наличия новых миграций
    if docker compose -f deployment/docker-compose.production.yml exec -T backend alembic current | grep -q "head"; then
        log "ℹ️  База данных уже актуальна"
    else
        log "🚀 Применение миграций..."
        docker compose -f deployment/docker-compose.production.yml exec -T backend alembic upgrade head
        log "✅ Миграции применены"
    fi
}

# =========================================
# 6. ПРОВЕРКА РАБОТОСПОСОБНОСТИ
# =========================================

health_check() {
    log "🏥 Проверка работоспособности..."
    
    # Проверка всех сервисов
    sleep 5
    
    # Backend
    if curl -s -f http://127.0.0.1:8000/health > /dev/null; then
        log "✅ Backend работает"
    else
        error "❌ Backend недоступен"
    fi
    
    # Frontend
    if curl -s -f http://127.0.0.1:3000 > /dev/null; then
        log "✅ Frontend работает"
    else
        error "❌ Frontend недоступен"
    fi
    
    # HTTPS сайт
    if curl -s -f https://lead-schem.ru > /dev/null; then
        log "✅ Сайт доступен по HTTPS"
    else
        warn "⚠️  Сайт недоступен по HTTPS"
    fi
    
    # Проверка API
    if curl -s -f https://lead-schem.ru/api/v1/health > /dev/null; then
        log "✅ API работает"
    else
        warn "⚠️  API недоступен"
    fi
    
    log "✅ Проверка работоспособности завершена"
}

# =========================================
# 7. ОЧИСТКА СТАРЫХ ДАННЫХ
# =========================================

cleanup() {
    log "🧹 Очистка старых данных..."
    
    # Удаление старых Docker образов
    docker image prune -f || warn "⚠️  Ошибка очистки Docker образов"
    
    # Удаление старых backup файлов (оставляем последние 5)
    find $BACKUP_DIR -name "*.gz" -type f -mtime +7 -delete || warn "⚠️  Ошибка очистки старых backup"
    find $BACKUP_DIR -name "env_backup_*" -type f | head -n -5 | xargs rm -f || true
    find $BACKUP_DIR -name "last_commit_*" -type f | head -n -5 | xargs rm -f || true
    
    log "✅ Очистка завершена"
}

# =========================================
# ROLLBACK ФУНКЦИЯ
# =========================================

rollback() {
    error "❌ Обновление не удалось, выполняем откат..."
    
    # Найти последний коммит
    LAST_COMMIT_FILE=$(ls -t $BACKUP_DIR/last_commit_* 2>/dev/null | head -1)
    if [ -f "$LAST_COMMIT_FILE" ]; then
        LAST_COMMIT=$(cat "$LAST_COMMIT_FILE")
        log "🔄 Откат к коммиту $LAST_COMMIT"
        git reset --hard $LAST_COMMIT
        
        # Перезапуск контейнеров
        docker compose -f deployment/docker-compose.production.yml restart
        
        log "✅ Откат завершен"
    else
        error "❌ Не удалось найти информацию о последнем коммите"
    fi
}

# =========================================
# ГЛАВНАЯ ФУНКЦИЯ
# =========================================

main() {
    log "🚀 Начинаем обновление приложения Lead Schema..."
    
    # Установка trap для отката в случае ошибки
    trap rollback ERR
    
    case "$1" in
        --quick)
            log "⚡ Быстрое обновление (без backup)"
            update_code
            update_containers
            health_check
            ;;
        --migrations-only)
            log "🔧 Только миграции"
            run_migrations
            ;;
        --no-backup)
            log "🚀 Полное обновление без backup"
            pre_update_check
            update_code
            update_containers
            run_migrations
            health_check
            cleanup
            ;;
        *)
            log "🔄 Полное обновление с backup"
            pre_update_check
            create_backup
            update_code
            update_containers
            run_migrations
            health_check
            cleanup
            ;;
    esac
    
    # Отключаем trap после успешного завершения
    trap - ERR
    
    echo ""
    log "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!"
    echo ""
    info "🌐 Сайт: https://lead-schem.ru"
    info "📊 Мониторинг: https://lead-schem.ru/monitoring/"
    info "📋 API Docs: https://lead-schem.ru/docs"
    echo ""
    
    # Показать статус контейнеров
    echo "=== Статус контейнеров ==="
    docker compose -f deployment/docker-compose.production.yml ps
}

# =========================================
# HELP
# =========================================

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  (без опций)      Полное обновление с backup"
    echo "  --quick          Быстрое обновление без backup"
    echo "  --migrations-only Только выполнение миграций"
    echo "  --no-backup     Полное обновление без backup"
    echo "  --help          Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0                    # Полное обновление"
    echo "  $0 --quick          # Быстрое обновление"
    echo "  $0 --migrations-only # Только миграции"
    exit 0
fi

# Запуск
main "$1" 