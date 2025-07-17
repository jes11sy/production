#!/bin/bash

# =============================================================================
# Скрипт проверки работоспособности LeadSchem Production
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

# Проверка статуса контейнеров
check_containers() {
    print_step "Проверка статуса контейнеров..."
    
    services=("backend" "frontend" "redis" "prometheus" "grafana" "nginx-proxy")
    all_ok=true
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.production.yml ps "$service" 2>/dev/null | grep -q "Up"; then
            print_success "Контейнер $service запущен"
        else
            print_error "Контейнер $service не запущен или недоступен"
            all_ok=false
        fi
    done
    
    return $([[ "$all_ok" == "true" ]] && echo 0 || echo 1)
}

# Проверка HTTP endpoints
check_endpoints() {
    print_step "Проверка HTTP endpoints..."
    
    endpoints=(
        "http://localhost:8000/health|Backend Health Check"
        "http://localhost:8000/api/v1/health|API Health Check"
        "http://localhost:3000|Frontend"
        "http://localhost:9090/-/healthy|Prometheus Health"
        "http://localhost:3001/api/health|Grafana Health"
    )
    
    all_ok=true
    
    for endpoint in "${endpoints[@]}"; do
        IFS='|' read -r url description <<< "$endpoint"
        
        if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
            print_success "$description доступен"
        else
            print_error "$description недоступен ($url)"
            all_ok=false
        fi
    done
    
    return $([[ "$all_ok" == "true" ]] && echo 0 || echo 1)
}

# Проверка базы данных
check_database() {
    print_step "Проверка базы данных..."
    
    # Попытка подключения к БД через backend
    if docker-compose -f docker-compose.production.yml exec -T backend python -c "
import asyncio
import sys
from app.core.database import get_db_session

async def test_db():
    try:
        async with get_db_session() as db:
            result = await db.execute('SELECT 1')
            print('Database connection OK')
            return True
    except Exception as e:
        print(f'Database error: {e}')
        return False

if asyncio.run(test_db()):
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null; then
        print_success "База данных доступна"
        return 0
    else
        print_error "Проблема с базой данных"
        return 1
    fi
}

# Проверка Redis
check_redis() {
    print_step "Проверка Redis..."
    
    if docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        print_success "Redis доступен"
        return 0
    else
        print_error "Redis недоступен"
        return 1
    fi
}

# Проверка использования ресурсов
check_resources() {
    print_step "Проверка использования ресурсов..."
    
    # Проверка использования диска
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        print_error "Критическое использование диска: ${disk_usage}%"
    elif [ "$disk_usage" -gt 80 ]; then
        print_warning "Высокое использование диска: ${disk_usage}%"
    else
        print_success "Использование диска: ${disk_usage}%"
    fi
    
    # Проверка использования памяти
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -gt 90 ]; then
        print_error "Критическое использование памяти: ${memory_usage}%"
    elif [ "$memory_usage" -gt 80 ]; then
        print_warning "Высокое использование памяти: ${memory_usage}%"
    else
        print_success "Использование памяти: ${memory_usage}%"
    fi
    
    # Проверка загрузки CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        print_error "Критическая загрузка CPU: ${cpu_usage}%"
    elif (( $(echo "$cpu_usage > 80" | bc -l) )); then
        print_warning "Высокая загрузка CPU: ${cpu_usage}%"
    else
        print_success "Загрузка CPU: ${cpu_usage}%"
    fi
}

# Проверка логов на ошибки
check_logs() {
    print_step "Проверка логов на критические ошибки..."
    
    # Проверка логов backend за последние 5 минут
    error_count=$(docker-compose -f docker-compose.production.yml logs --since=5m backend 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
    
    if [ "$error_count" -gt 10 ]; then
        print_error "Найдено $error_count ошибок в логах backend за последние 5 минут"
    elif [ "$error_count" -gt 0 ]; then
        print_warning "Найдено $error_count ошибок в логах backend за последние 5 минут"
    else
        print_success "Критических ошибок в логах не найдено"
    fi
}

# Проверка SSL сертификатов
check_ssl() {
    print_step "Проверка SSL сертификатов..."
    
    cert_path="/etc/letsencrypt/live/lead-schem.ru/fullchain.pem"
    
    if [ -f "$cert_path" ]; then
        # Проверка срока действия сертификата
        expiry_date=$(openssl x509 -enddate -noout -in "$cert_path" | cut -d= -f2)
        expiry_timestamp=$(date -d "$expiry_date" +%s)
        current_timestamp=$(date +%s)
        days_left=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ "$days_left" -lt 7 ]; then
            print_error "SSL сертификат истекает через $days_left дней!"
        elif [ "$days_left" -lt 30 ]; then
            print_warning "SSL сертификат истекает через $days_left дней"
        else
            print_success "SSL сертификат действителен еще $days_left дней"
        fi
    else
        print_warning "SSL сертификат не найден"
    fi
}

# Полная проверка
main() {
    echo "=================================================="
    echo "🏥 ПРОВЕРКА РАБОТОСПОСОБНОСТИ LEADSCHEM"
    echo "=================================================="
    echo ""
    
    # Переход в папку deployment
    cd "$(dirname "$0")"
    
    overall_status=0
    
    # Выполнение всех проверок
    check_containers || overall_status=1
    echo ""
    
    check_endpoints || overall_status=1
    echo ""
    
    check_database || overall_status=1
    echo ""
    
    check_redis || overall_status=1
    echo ""
    
    check_resources
    echo ""
    
    check_logs
    echo ""
    
    check_ssl
    echo ""
    
    # Финальный статус
    echo "=================================================="
    if [ $overall_status -eq 0 ]; then
        print_success "🎉 ВСЕ СЕРВИСЫ РАБОТАЮТ НОРМАЛЬНО!"
    else
        print_error "⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ - ТРЕБУЕТСЯ ВНИМАНИЕ!"
    fi
    echo "=================================================="
    
    # Дополнительная информация
    echo ""
    echo "🔧 Полезные команды для диагностики:"
    echo "   Логи всех сервисов: docker-compose -f docker-compose.production.yml logs -f"
    echo "   Статус контейнеров: docker-compose -f docker-compose.production.yml ps"
    echo "   Ресурсы контейнеров: docker stats"
    echo "   Перезапуск сервиса: docker-compose -f docker-compose.production.yml restart <service>"
    
    exit $overall_status
}

main "$@" 