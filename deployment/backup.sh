#!/bin/bash

# =============================================================================
# Скрипт резервного копирования LeadSchem Production
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "${BLUE}📋 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Настройки
BACKUP_DIR="../backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="leadschem_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

main() {
    print_step "Создание резервной копии LeadSchem..."
    
    # Переход в папку deployment
    cd "$(dirname "$0")"
    
    # Создание директории бэкапов
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_PATH"
    
    # Бэкап конфигурации
    print_step "Резервное копирование конфигурации..."
    cp -r . "$BACKUP_PATH/deployment/" 2>/dev/null || true
    
    # Бэкап медиафайлов
    if [ -d "../media" ]; then
        print_step "Резервное копирование медиафайлов..."
        cp -r ../media "$BACKUP_PATH/" 2>/dev/null || true
    fi
    
    # Бэкап логов
    if [ -d "../logs" ]; then
        print_step "Резервное копирование логов..."
        cp -r ../logs "$BACKUP_PATH/" 2>/dev/null || true
    fi
    
    # Бэкап базы данных
    print_step "Резервное копирование базы данных..."
    if docker-compose -f docker-compose.production.yml ps postgres | grep -q "Up"; then
        docker-compose -f docker-compose.production.yml exec -T postgres pg_dump \
            -U leadschem_user leadschem_db > "$BACKUP_PATH/database_dump.sql" 2>/dev/null || true
    else
        print_warning "PostgreSQL не запущен, пропускаем бэкап БД"
    fi
    
    # Создание архива
    print_step "Создание архива..."
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME/" && rm -rf "$BACKUP_NAME/"
    
    # Информация о бэкапе
    BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    
    print_success "Резервная копия создана:"
    echo "📁 Файл: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    echo "📊 Размер: $BACKUP_SIZE"
    echo "📅 Дата: $(date)"
    
    # Очистка старых бэкапов (оставляем последние 10)
    print_step "Очистка старых бэкапов..."
    ls -t leadschem_backup_*.tar.gz | tail -n +11 | xargs -r rm
    
    print_success "Резервное копирование завершено!"
}

main "$@" 