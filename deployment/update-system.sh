#!/bin/bash

# =============================================================================
# Скрипт обновления LeadSchem Production
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

# Проверка Git репозитория
check_git() {
    print_step "Проверка Git репозитория..."
    
    if [ ! -d "../.git" ]; then
        print_error "Git репозиторий не найден!"
        exit 1
    fi
    
    # Проверка незакоммиченных изменений
    if ! git diff --exit-code --quiet || ! git diff --cached --exit-code --quiet; then
        print_warning "Обнаружены незакоммиченные изменения!"
        print_warning "Рекомендуется сохранить изменения перед обновлением."
        
        read -p "Продолжить обновление? (y/N): " continue_update
        if [[ ! "$continue_update" =~ ^[Yy]$ ]]; then
            print_step "Обновление отменено пользователем"
            exit 0
        fi
    fi
    
    print_success "Git репозиторий проверен"
}

# Создание резервной копии
create_backup() {
    print_step "Создание резервной копии перед обновлением..."
    
    if [ -x "./backup.sh" ]; then
        ./backup.sh
    else
        print_warning "Скрипт backup.sh не найден, пропускаем резервное копирование"
    fi
}

# Остановка сервисов
stop_services() {
    print_step "Остановка сервисов..."
    
    docker-compose -f docker-compose.production.yml down
    
    print_success "Сервисы остановлены"
}

# Обновление кода
update_code() {
    print_step "Обновление кода из Git репозитория..."
    
    cd ..
    
    # Получение изменений
    git fetch origin
    
    # Показ изменений
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
        print_step "Доступны следующие обновления:"
        git log --oneline HEAD..origin/main
        echo ""
        
        read -p "Применить обновления? (Y/n): " apply_updates
        if [[ "$apply_updates" =~ ^[Nn]$ ]]; then
            print_step "Обновление отменено пользователем"
            cd deployment
            return 1
        fi
        
        # Применение обновлений
        git pull origin main
        print_success "Код обновлен"
    else
        print_success "Код уже актуален"
    fi
    
    cd deployment
}

# Пересборка образов
rebuild_images() {
    print_step "Пересборка Docker образов..."
    
    # Очистка старых образов
    docker system prune -f
    
    # Пересборка образов
    docker-compose -f docker-compose.production.yml build --no-cache
    
    print_success "Образы пересобраны"
}

# Запуск сервисов
start_services() {
    print_step "Запуск обновленных сервисов..."
    
    # Запуск сервисов
    docker-compose -f docker-compose.production.yml --env-file env.production.lead-schem up -d
    
    # Ожидание запуска
    sleep 30
    
    print_success "Сервисы запущены"
}

# Выполнение миграций
run_migrations() {
    print_step "Выполнение миграций базы данных..."
    
    # Ожидание готовности backend
    sleep 15
    
    # Выполнение миграций
    docker-compose -f docker-compose.production.yml exec backend python -m alembic upgrade head
    
    print_success "Миграции выполнены"
}

# Проверка работоспособности
health_check() {
    print_step "Проверка работоспособности после обновления..."
    
    if [ -x "./health-check.sh" ]; then
        ./health-check.sh
    else
        print_warning "Скрипт health-check.sh не найден, выполняем базовую проверку"
        
        # Базовая проверка endpoints
        endpoints=(
            "http://localhost:8000/health"
            "http://localhost:3000"
        )
        
        for endpoint in "${endpoints[@]}"; do
            if curl -f -s --max-time 10 "$endpoint" > /dev/null; then
                print_success "Endpoint $endpoint доступен"
            else
                print_error "Endpoint $endpoint недоступен"
                return 1
            fi
        done
    fi
}

# Очистка
cleanup() {
    print_step "Очистка неиспользуемых ресурсов..."
    
    # Очистка Docker
    docker system prune -f
    docker volume prune -f
    
    print_success "Очистка завершена"
}

# Основная функция
main() {
    echo "=================================================="
    echo "🔄 ОБНОВЛЕНИЕ LEADSCHEM PRODUCTION"
    echo "=================================================="
    echo ""
    
    # Переход в папку deployment
    cd "$(dirname "$0")"
    
    # Проверка что мы в правильной директории
    if [ ! -f "docker-compose.production.yml" ]; then
        print_error "Файл docker-compose.production.yml не найден!"
        print_error "Убедитесь что скрипт запускается из папки deployment/"
        exit 1
    fi
    
    # Выполнение всех шагов
    check_git
    create_backup
    stop_services
    
    if update_code; then
        rebuild_images
        start_services
        run_migrations
        health_check
        cleanup
        
        echo ""
        echo "=================================================="
        print_success "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!"
        echo "=================================================="
        
        echo ""
        print_step "Информация о системе:"
        echo "🌐 Frontend: http://localhost:3000"
        echo "🔧 Backend API: http://localhost:8000"
        echo "📊 Monitoring: http://localhost:3001"
        echo ""
        print_step "Полезные команды:"
        echo "   Логи: docker-compose -f docker-compose.production.yml logs -f"
        echo "   Статус: docker-compose -f docker-compose.production.yml ps"
        echo "   Проверка здоровья: ./health-check.sh"
    else
        print_step "Перезапуск сервисов без обновления кода..."
        start_services
    fi
}

# Обработка ошибок
trap 'echo -e "\n${RED}❌ Обновление прервано из-за ошибки!${NC}"; echo "Перезапуск сервисов..."; docker-compose -f docker-compose.production.yml --env-file env.production.lead-schem up -d' ERR

main "$@" 