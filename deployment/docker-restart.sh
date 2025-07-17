#!/bin/bash

# Docker Restart Script для LeadSchem CRM
# Скрипт для жесткого перезапуска сервисов с полной очисткой кэша

set -e

COMPOSE_FILE="docker-compose.production.yml"
PROJECT_NAME="leadschem"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Проверка что мы в правильной директории
check_directory() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Файл $COMPOSE_FILE не найден. Убедитесь что вы в директории deployment/"
        exit 1
    fi
}

# Функция полной очистки проекта
cleanup_project() {
    log "🧹 Полная очистка проекта..."
    
    # Остановить все сервисы
    docker-compose -f $COMPOSE_FILE down --remove-orphans || true
    
    # Удалить все образы проекта
    docker images | grep $PROJECT_NAME | awk '{print $3}' | xargs -r docker rmi -f || true
    
    # Удалить неиспользуемые образы и кэш
    docker system prune -f || true
    docker builder prune -f || true
    
    log "✅ Очистка завершена"
}

# Функция очистки конкретного сервиса
cleanup_service() {
    local service=$1
    log "🧹 Очистка сервиса: $service"
    
    # Остановить сервис
    docker-compose -f $COMPOSE_FILE stop $service || true
    docker-compose -f $COMPOSE_FILE rm -f $service || true
    
    # Удалить образ сервиса
    local image_name="${PROJECT_NAME}_${service}"
    docker images | grep $image_name | awk '{print $3}' | xargs -r docker rmi -f || true
    
    log "✅ Очистка $service завершена"
}

# 1. Полный перезапуск проекта
restart_full() {
    log "🚀 Начинаем ПОЛНЫЙ перезапуск проекта..."
    
    cleanup_project
    
    log "🔨 Пересборка всех образов..."
    docker-compose -f $COMPOSE_FILE build --no-cache --force-rm
    
    log "▶️ Запуск всех сервисов..."
    docker-compose -f $COMPOSE_FILE up -d
    
    log "📊 Проверка статуса сервисов..."
    docker-compose -f $COMPOSE_FILE ps
    
    log "🎉 ПОЛНЫЙ перезапуск завершен!"
}

# 2. Перезапуск фронтенда
restart_frontend() {
    log "🎨 Перезапуск ФРОНТЕНДА..."
    
    cleanup_service "frontend"
    
    log "🔨 Пересборка frontend образа..."
    docker-compose -f $COMPOSE_FILE build frontend --no-cache --force-rm
    
    log "▶️ Запуск frontend..."
    docker-compose -f $COMPOSE_FILE up -d frontend
    
    log "📊 Статус frontend:"
    docker-compose -f $COMPOSE_FILE ps frontend
    
    log "🎉 Перезапуск frontend завершен!"
}

# 3. Перезапуск бэкенда
restart_backend() {
    log "⚙️ Перезапуск БЭКЕНДА..."
    
    cleanup_service "backend"
    
    log "🔨 Пересборка backend образа..."
    docker-compose -f $COMPOSE_FILE build backend --no-cache --force-rm
    
    log "▶️ Запуск backend..."
    docker-compose -f $COMPOSE_FILE up -d backend
    
    log "📊 Статус backend:"
    docker-compose -f $COMPOSE_FILE ps backend
    
    log "🎉 Перезапуск backend завершен!"
}

# 4. Перезапуск nginx
restart_nginx() {
    log "🌐 Перезапуск NGINX..."
    
    cleanup_service "nginx-proxy"
    
    log "▶️ Запуск nginx..."
    docker-compose -f $COMPOSE_FILE up -d nginx-proxy
    
    log "📊 Статус nginx:"
    docker-compose -f $COMPOSE_FILE ps nginx-proxy
    
    log "🎉 Перезапуск nginx завершен!"
}

# 5. Перезапуск Redis
restart_redis() {
    log "📦 Перезапуск REDIS..."
    
    cleanup_service "redis"
    
    log "▶️ Запуск redis..."
    docker-compose -f $COMPOSE_FILE up -d redis
    
    log "📊 Статус redis:"
    docker-compose -f $COMPOSE_FILE ps redis
    
    log "🎉 Перезапуск redis завершен!"
}

# 6. Перезапуск мониторинга (Grafana + Prometheus)
restart_monitoring() {
    log "📈 Перезапуск МОНИТОРИНГА..."
    
    cleanup_service "grafana"
    cleanup_service "prometheus"
    
    log "▶️ Запуск мониторинга..."
    docker-compose -f $COMPOSE_FILE up -d grafana prometheus
    
    log "📊 Статус мониторинга:"
    docker-compose -f $COMPOSE_FILE ps grafana prometheus
    
    log "🎉 Перезапуск мониторинга завершен!"
}

# 7. Просмотр логов
show_logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        log "📋 Логи сервиса $service:"
        docker-compose -f $COMPOSE_FILE logs $service --tail=20
    else
        log "📋 Логи всех сервисов:"
        docker-compose -f $COMPOSE_FILE logs --tail=10
    fi
}

# 8. Проверка статуса
status() {
    log "📊 Статус всех сервисов:"
    docker-compose -f $COMPOSE_FILE ps
    
    log "💾 Использование Docker:"
    docker system df
}

# 9. Быстрый перезапуск (без пересборки)
quick_restart() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        log "⚡ Быстрый перезапуск $service..."
        docker-compose -f $COMPOSE_FILE restart $service
        docker-compose -f $COMPOSE_FILE ps $service
    else
        log "⚡ Быстрый перезапуск всех сервисов..."
        docker-compose -f $COMPOSE_FILE restart
        docker-compose -f $COMPOSE_FILE ps
    fi
}

# Функция помощи
show_help() {
    echo -e "${BLUE}🚀 Docker Restart Script для LeadSchem CRM${NC}"
    echo ""
    echo -e "${YELLOW}ИСПОЛЬЗОВАНИЕ:${NC}"
    echo "  $0 <команда> [параметры]"
    echo ""
    echo -e "${YELLOW}КОМАНДЫ:${NC}"
    echo -e "  ${GREEN}full${NC}           - Полный перезапуск (удаление образов + пересборка)"
    echo -e "  ${GREEN}frontend${NC}       - Перезапуск только фронтенда"
    echo -e "  ${GREEN}backend${NC}        - Перезапуск только бэкенда"
    echo -e "  ${GREEN}nginx${NC}          - Перезапуск только nginx"
    echo -e "  ${GREEN}redis${NC}          - Перезапуск только redis"
    echo -e "  ${GREEN}monitoring${NC}     - Перезапуск Grafana + Prometheus"
    echo -e "  ${GREEN}logs [service]${NC} - Показать логи (всех или конкретного сервиса)"
    echo -e "  ${GREEN}status${NC}         - Показать статус всех сервисов"
    echo -e "  ${GREEN}quick [service]${NC}- Быстрый перезапуск без пересборки"
    echo -e "  ${GREEN}help${NC}           - Показать эту справку"
    echo ""
    echo -e "${YELLOW}ПРИМЕРЫ:${NC}"
    echo "  $0 full                    # Полный перезапуск"
    echo "  $0 frontend               # Перезапуск только фронтенда"
    echo "  $0 logs backend           # Логи бэкенда"
    echo "  $0 quick nginx            # Быстрый перезапуск nginx"
    echo ""
}

# Основная логика
main() {
    check_directory
    
    case "${1:-help}" in
        "full")
            restart_full
            ;;
        "frontend")
            restart_frontend
            ;;
        "backend")
            restart_backend
            ;;
        "nginx")
            restart_nginx
            ;;
        "redis")
            restart_redis
            ;;
        "monitoring")
            restart_monitoring
            ;;
        "logs")
            show_logs "$2"
            ;;
        "status")
            status
            ;;
        "quick")
            quick_restart "$2"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            error "Неизвестная команда: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Запуск скрипта
main "$@" 