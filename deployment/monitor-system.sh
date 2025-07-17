#!/bin/bash

# =========================================
# 📊 МОНИТОРИНГ СОСТОЯНИЯ СИСТЕМЫ
# =========================================

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

PROJECT_DIR="/opt/leadschem"

# =========================================
# ПРОВЕРКА СИСТЕМНЫХ РЕСУРСОВ
# =========================================

check_system_resources() {
    echo -e "${PURPLE}=== 💻 СИСТЕМНЫЕ РЕСУРСЫ ===${NC}"
    
    # CPU загрузка
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | cut -d',' -f1 | xargs)
    
    if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
        warn "CPU загрузка: ${CPU_USAGE}% (высокая нагрузка)"
    else
        log "CPU загрузка: ${CPU_USAGE}%"
    fi
    
    log "Load Average: $CPU_LOAD"
    
    # Память
    MEMORY_INFO=$(free -h | grep "Mem:")
    MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
    MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
    MEMORY_PERCENT=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    
    if (( $(echo "$MEMORY_PERCENT > 85" | bc -l) )); then
        warn "Память: ${MEMORY_USED}/${MEMORY_TOTAL} (${MEMORY_PERCENT}% - высокое использование)"
    else
        log "Память: ${MEMORY_USED}/${MEMORY_TOTAL} (${MEMORY_PERCENT}%)"
    fi
    
    # Дисковое пространство
    echo ""
    info "Дисковое пространство:"
    df -h | grep -E "(Filesystem|/dev/)" | while read line; do
        if echo "$line" | grep -q "Filesystem"; then
            continue
        fi
        
        USAGE=$(echo "$line" | awk '{print $5}' | cut -d'%' -f1)
        MOUNT=$(echo "$line" | awk '{print $6}')
        
        if [ "$USAGE" -gt 85 ]; then
            warn "  $line (критический уровень)"
        elif [ "$USAGE" -gt 70 ]; then
            warn "  $line (предупреждение)"
        else
            log "  $line"
        fi
    done
    
    echo ""
}

# =========================================
# ПРОВЕРКА DOCKER КОНТЕЙНЕРОВ
# =========================================

check_docker_containers() {
    echo -e "${PURPLE}=== 🐳 DOCKER КОНТЕЙНЕРЫ ===${NC}"
    
    if [ ! -d "$PROJECT_DIR" ]; then
        error "Директория проекта не найдена: $PROJECT_DIR"
        return 1
    fi
    
    cd $PROJECT_DIR
    
    # Статус контейнеров
    CONTAINERS=$(docker compose -f deployment/docker-compose.production.yml ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}")
    
    echo "$CONTAINERS" | while IFS=$'\t' read -r service status ports; do
        if [ "$service" == "SERVICE" ]; then
            continue
        fi
        
        if echo "$status" | grep -q "Up"; then
            log "$service: $status"
        else
            error "$service: $status"
        fi
    done
    
    echo ""
    
    # Использование ресурсов контейнерами
    info "Использование ресурсов контейнерами:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -10
    
    echo ""
}

# =========================================
# ПРОВЕРКА СЕТЕВЫХ СЕРВИСОВ
# =========================================

check_network_services() {
    echo -e "${PURPLE}=== 🌐 СЕТЕВЫЕ СЕРВИСЫ ===${NC}"
    
    # Локальные сервисы
    info "Проверка локальных сервисов:"
    
    # Backend
    if curl -s -f --connect-timeout 5 http://127.0.0.1:8000/health > /dev/null; then
        log "Backend API (8000): доступен"
    else
        error "Backend API (8000): недоступен"
    fi
    
    # Frontend
    if curl -s -f --connect-timeout 5 http://127.0.0.1:3000 > /dev/null; then
        log "Frontend (3000): доступен"
    else
        error "Frontend (3000): недоступен"
    fi
    
    # Redis
    if docker compose -f $PROJECT_DIR/deployment/docker-compose.production.yml exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log "Redis: доступен"
    else
        error "Redis: недоступен"
    fi
    
    # PostgreSQL (внешняя БД)
    if [ -f "$PROJECT_DIR/.env" ]; then
        source $PROJECT_DIR/.env
        if PGPASSWORD="$POSTGRESQL_PASSWORD" timeout 10 psql -h "$POSTGRESQL_HOST" -U "$POSTGRESQL_USER" -d "$POSTGRESQL_DBNAME" -c "SELECT 1;" > /dev/null 2>&1; then
            log "PostgreSQL: доступна"
        else
            error "PostgreSQL: недоступна"
        fi
    fi
    
    echo ""
    info "Проверка внешних сервисов:"
    
    # HTTPS сайт
    if curl -s -f --connect-timeout 10 https://lead-schem.ru > /dev/null; then
        log "HTTPS сайт: доступен"
    else
        error "HTTPS сайт: недоступен"
    fi
    
    # API через HTTPS
    if curl -s -f --connect-timeout 10 https://lead-schem.ru/api/v1/health > /dev/null; then
        log "API через HTTPS: доступен"
    else
        error "API через HTTPS: недоступен"
    fi
    
    echo ""
}

# =========================================
# ПРОВЕРКА NGINX И SSL
# =========================================

check_nginx_ssl() {
    echo -e "${PURPLE}=== 🔒 NGINX И SSL ===${NC}"
    
    # Статус Nginx
    if systemctl is-active --quiet nginx; then
        log "Nginx: запущен"
    else
        error "Nginx: не запущен"
    fi
    
    # Проверка конфигурации Nginx
    if nginx -t &>/dev/null; then
        log "Конфигурация Nginx: корректная"
    else
        error "Конфигурация Nginx: содержит ошибки"
    fi
    
    # SSL сертификаты
    if [ -f "/etc/letsencrypt/live/lead-schem.ru/fullchain.pem" ]; then
        CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/lead-schem.ru/fullchain.pem | cut -d= -f2)
        CERT_EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_UNTIL_EXPIRY=$(( (CERT_EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
        
        if [ $DAYS_UNTIL_EXPIRY -lt 7 ]; then
            error "SSL сертификат истекает через $DAYS_UNTIL_EXPIRY дней"
        elif [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
            warn "SSL сертификат истекает через $DAYS_UNTIL_EXPIRY дней"
        else
            log "SSL сертификат действует ($DAYS_UNTIL_EXPIRY дней до истечения)"
        fi
    else
        error "SSL сертификат не найден"
    fi
    
    echo ""
}

# =========================================
# ПРОВЕРКА ЛОГОВ
# =========================================

check_logs() {
    echo -e "${PURPLE}=== 📝 АНАЛИЗ ЛОГОВ ===${NC}"
    
    cd $PROJECT_DIR
    
    # Последние ошибки в логах контейнеров
    info "Последние ошибки в логах (за последний час):"
    
    # Backend ошибки
    BACKEND_ERRORS=$(docker compose -f deployment/docker-compose.production.yml logs --since=1h backend 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
    if [ $BACKEND_ERRORS -gt 0 ]; then
        warn "Backend: $BACKEND_ERRORS ошибок за последний час"
        docker compose -f deployment/docker-compose.production.yml logs --since=1h --tail=5 backend | grep -i "error\|exception\|critical" | tail -3
    else
        log "Backend: ошибок не обнаружено"
    fi
    
    # Frontend ошибки
    FRONTEND_ERRORS=$(docker compose -f deployment/docker-compose.production.yml logs --since=1h frontend 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
    if [ $FRONTEND_ERRORS -gt 0 ]; then
        warn "Frontend: $FRONTEND_ERRORS ошибок за последний час"
    else
        log "Frontend: ошибок не обнаружено"
    fi
    
    # Nginx ошибки
    if [ -f "/var/log/nginx/error.log" ]; then
        NGINX_ERRORS=$(tail -100 /var/log/nginx/error.log | grep "$(date '+%Y/%m/%d %H')" | wc -l)
        if [ $NGINX_ERRORS -gt 0 ]; then
            warn "Nginx: $NGINX_ERRORS ошибок за последний час"
        else
            log "Nginx: ошибок не обнаружено"
        fi
    fi
    
    echo ""
}

# =========================================
# ПРОВЕРКА БАЗЫ ДАННЫХ
# =========================================

check_database() {
    echo -e "${PURPLE}=== 🗄️ БАЗА ДАННЫХ ===${NC}"
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        source $PROJECT_DIR/.env
        
        # Размер базы данных
        DB_SIZE=$(PGPASSWORD="$POSTGRESQL_PASSWORD" psql -h "$POSTGRESQL_HOST" -U "$POSTGRESQL_USER" -d "$POSTGRESQL_DBNAME" -t -c "SELECT pg_size_pretty(pg_database_size('$POSTGRESQL_DBNAME'));" 2>/dev/null | xargs)
        if [ $? -eq 0 ]; then
            log "Размер базы данных: $DB_SIZE"
        else
            error "Не удалось получить размер базы данных"
        fi
        
        # Количество подключений
        CONNECTIONS=$(PGPASSWORD="$POSTGRESQL_PASSWORD" psql -h "$POSTGRESQL_HOST" -U "$POSTGRESQL_USER" -d "$POSTGRESQL_DBNAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='$POSTGRESQL_DBNAME';" 2>/dev/null | xargs)
        if [ $? -eq 0 ]; then
            if [ $CONNECTIONS -gt 80 ]; then
                warn "Активных подключений: $CONNECTIONS (высокая нагрузка)"
            else
                log "Активных подключений: $CONNECTIONS"
            fi
        fi
        
        # Последняя миграция
        MIGRATION=$(docker compose -f $PROJECT_DIR/deployment/docker-compose.production.yml exec -T backend alembic current 2>/dev/null | tail -1)
        if [ $? -eq 0 ]; then
            log "Текущая миграция: $MIGRATION"
        else
            warn "Не удалось получить информацию о миграциях"
        fi
    fi
    
    echo ""
}

# =========================================
# ПРОВЕРКА BACKUP
# =========================================

check_backups() {
    echo -e "${PURPLE}=== 💾 РЕЗЕРВНЫЕ КОПИИ ===${NC}"
    
    BACKUP_DIR="/opt/leadschem/backups"
    
    if [ -d "$BACKUP_DIR" ]; then
        # Последний backup
        LAST_BACKUP=$(ls -t $BACKUP_DIR/*.gz 2>/dev/null | head -1)
        if [ -n "$LAST_BACKUP" ]; then
            BACKUP_DATE=$(stat -c %y "$LAST_BACKUP" | cut -d' ' -f1)
            BACKUP_SIZE=$(ls -lh "$LAST_BACKUP" | awk '{print $5}')
            DAYS_AGO=$(( ($(date +%s) - $(stat -c %Y "$LAST_BACKUP")) / 86400 ))
            
            if [ $DAYS_AGO -gt 3 ]; then
                warn "Последний backup: $BACKUP_DATE ($DAYS_AGO дней назад, $BACKUP_SIZE)"
            else
                log "Последний backup: $BACKUP_DATE ($DAYS_AGO дней назад, $BACKUP_SIZE)"
            fi
        else
            error "Backup файлы не найдены"
        fi
        
        # Количество backup файлов
        BACKUP_COUNT=$(ls $BACKUP_DIR/*.gz 2>/dev/null | wc -l)
        log "Всего backup файлов: $BACKUP_COUNT"
        
        # Размер всех backup
        TOTAL_SIZE=$(du -sh $BACKUP_DIR 2>/dev/null | cut -f1)
        log "Общий размер backup: $TOTAL_SIZE"
    else
        error "Директория backup не существует: $BACKUP_DIR"
    fi
    
    echo ""
}

# =========================================
# СВОДКА СОСТОЯНИЯ
# =========================================

show_summary() {
    echo -e "${CYAN}=== 📋 СВОДКА СОСТОЯНИЯ ===${NC}"
    
    UPTIME=$(uptime -p)
    log "Время работы системы: $UPTIME"
    
    # Подсчет проблем
    ISSUES=0
    
    # Проверяем основные сервисы
    if ! curl -s -f --connect-timeout 5 https://lead-schem.ru > /dev/null; then
        ((ISSUES++))
    fi
    
    if ! systemctl is-active --quiet nginx; then
        ((ISSUES++))
    fi
    
    if ! docker compose -f $PROJECT_DIR/deployment/docker-compose.production.yml ps | grep -q "Up"; then
        ((ISSUES++))
    fi
    
    if [ $ISSUES -eq 0 ]; then
        log "Общее состояние: ВСЕ СЕРВИСЫ РАБОТАЮТ НОРМАЛЬНО ✅"
    elif [ $ISSUES -eq 1 ]; then
        warn "Общее состояние: ОБНАРУЖЕНА 1 ПРОБЛЕМА ⚠️"
    else
        error "Общее состояние: ОБНАРУЖЕНО $ISSUES ПРОБЛЕМ ❌"
    fi
    
    echo ""
    info "Для детального мониторинга посетите: https://lead-schem.ru/monitoring/"
    echo ""
}

# =========================================
# ГЛАВНАЯ ФУНКЦИЯ
# =========================================

main() {
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║               📊 МОНИТОРИНГ LEAD-SCHEM                      ║${NC}"
    echo -e "${CYAN}║                    $(date)                     ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    case "$1" in
        --system)
            check_system_resources
            ;;
        --docker)
            check_docker_containers
            ;;
        --network)
            check_network_services
            ;;
        --nginx)
            check_nginx_ssl
            ;;
        --logs)
            check_logs
            ;;
        --database)
            check_database
            ;;
        --backup)
            check_backups
            ;;
        --quick)
            check_docker_containers
            check_network_services
            show_summary
            ;;
        *)
            # Полная проверка
            check_system_resources
            check_docker_containers
            check_network_services
            check_nginx_ssl
            check_database
            check_logs
            check_backups
            show_summary
            ;;
    esac
}

# =========================================
# HELP
# =========================================

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  (без опций)  Полная проверка всех компонентов"
    echo "  --system     Только системные ресурсы"
    echo "  --docker     Только Docker контейнеры"
    echo "  --network    Только сетевые сервисы"
    echo "  --nginx      Только Nginx и SSL"
    echo "  --logs       Только анализ логов"
    echo "  --database   Только база данных"
    echo "  --backup     Только резервные копии"
    echo "  --quick      Быстрая проверка (Docker + сеть + сводка)"
    echo "  --help       Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0               # Полная диагностика"
    echo "  $0 --quick      # Быстрая проверка"
    echo "  $0 --logs       # Только ошибки в логах"
    exit 0
fi

# Запуск
main "$1" 