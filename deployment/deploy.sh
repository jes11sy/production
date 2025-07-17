#!/bin/bash
# Главный скрипт развертывания lead-schem.ru
# Полная автоматизация развертывания на сервере 194.87.201.221

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Проверка запуска от root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен от root"
fi

# Переменные
PROJECT_DIR="/opt/leadschem"
REPOSITORY_URL="https://github.com/your-repo/leadschem.git"  # Замените на ваш репозиторий
DOMAIN="lead-schem.ru"

log "🚀 Начинаем полное развертывание lead-schem.ru..."
log "📍 Сервер: 194.87.201.221"
log "🌐 Домен: $DOMAIN"
log "📁 Проект: $PROJECT_DIR"

# Меню выбора действий
echo ""
echo "Выберите действие:"
echo "1) Полная установка (новый сервер)"
echo "2) Только развертывание приложения"
echo "3) Обновление приложения"
echo "4) Настройка SSL"
echo "5) Перезапуск сервисов"
echo "6) Проверка статуса"
echo "7) Просмотр логов"
echo "8) Backup базы данных"
read -p "Введите номер (1-8): " choice

case $choice in
    1)
        log "🔧 Выбрана полная установка..."
        FULL_INSTALL=true
        ;;
    2)
        log "📦 Выбрано развертывание приложения..."
        DEPLOY_ONLY=true
        ;;
    3)
        log "🔄 Выбрано обновление приложения..."
        UPDATE_ONLY=true
        ;;
    4)
        log "🔒 Выбрана настройка SSL..."
        SSL_ONLY=true
        ;;
    5)
        log "♻️ Выбран перезапуск сервисов..."
        RESTART_ONLY=true
        ;;
    6)
        log "📊 Выбрана проверка статуса..."
        STATUS_ONLY=true
        ;;
    7)
        log "📋 Выбран просмотр логов..."
        LOGS_ONLY=true
        ;;
    8)
        log "💾 Выбран backup базы данных..."
        BACKUP_ONLY=true
        ;;
    *)
        error "Неверный выбор"
        ;;
esac

# Функция полной установки
full_install() {
    log "🔧 Начинаем полную установку сервера..."
    
    # Запуск скрипта установки сервера
    if [ -f "server-setup.sh" ]; then
        chmod +x server-setup.sh
        ./server-setup.sh
    else
        error "Файл server-setup.sh не найден"
    fi
    
    log "✅ Базовая установка сервера завершена"
}

# Функция клонирования репозитория
clone_repository() {
    log "📥 Клонирование репозитория..."
    
    if [ -d "$PROJECT_DIR" ]; then
        warn "Директория $PROJECT_DIR уже существует"
        read -p "Удалить и пересоздать? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf $PROJECT_DIR
        else
            return 0
        fi
    fi
    
    # Создаем директорию и клонируем
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    
    # Если репозиторий не настроен, копируем локальные файлы
    if [ -d "/tmp/leadschem" ]; then
        log "📋 Копирование локальных файлов..."
        cp -r /tmp/leadschem/* $PROJECT_DIR/
    else
        warn "Репозиторий не настроен. Скопируйте файлы проекта в $PROJECT_DIR"
        return 1
    fi
    
    chown -R leadschem:leadschem $PROJECT_DIR
}

# Функция сборки приложения
build_application() {
    log "🔨 Сборка приложения..."
    
    cd $PROJECT_DIR
    
    # Сборка backend
    log "🐍 Сборка backend..."
    cd backend
    docker build -f deployment/Dockerfile -t leadschem-backend .
    
    # Сборка frontend
    log "⚛️ Сборка frontend..."
    cd ../frontend
    docker build -f Dockerfile.production -t leadschem-frontend \
        --build-arg VITE_API_URL=https://$DOMAIN/api/v1 .
    
    cd ..
}

# Функция развертывания
deploy_application() {
    log "🚀 Развертывание приложения..."
    
    cd $PROJECT_DIR/deployment
    
    # Остановка существующих контейнеров
    log "⏹️ Остановка существующих сервисов..."
    docker-compose -f docker-compose.production.yml down || true
    
    # Запуск новых контейнеров
    log "▶️ Запуск новых сервисов..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Ожидание запуска
    log "⏳ Ожидание запуска сервисов..."
    sleep 30
    
    # Проверка статуса
    docker-compose -f docker-compose.production.yml ps
}

# Функция настройки SSL
setup_ssl() {
    log "🔒 Настройка SSL..."
    
    if [ -f "$PROJECT_DIR/deployment/setup-ssl.sh" ]; then
        chmod +x $PROJECT_DIR/deployment/setup-ssl.sh
        $PROJECT_DIR/deployment/setup-ssl.sh
    else
        error "Файл setup-ssl.sh не найден"
    fi
}

# Функция проверки статуса
check_status() {
    log "📊 Проверка статуса сервисов..."
    
    echo ""
    echo "=== Docker контейнеры ==="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "=== Nginx статус ==="
    systemctl status nginx --no-pager
    
    echo ""
    echo "=== Проверка доступности ==="
    if curl -s http://127.0.0.1:8000/api/v1/health > /dev/null; then
        log "✅ Backend API доступен"
    else
        warn "❌ Backend API недоступен"
    fi
    
    if curl -s http://127.0.0.1:3000 > /dev/null; then
        log "✅ Frontend доступен"
    else
        warn "❌ Frontend недоступен"
    fi
    
    if curl -s https://$DOMAIN > /dev/null; then
        log "✅ Сайт доступен по HTTPS"
    else
        warn "❌ Сайт недоступен по HTTPS"
    fi
    
    echo ""
    echo "=== Ресурсы системы ==="
    df -h / | grep -v Filesystem
    free -h | grep Mem
    
    echo ""
    echo "=== Логи ошибок ==="
    tail -5 /var/log/nginx/lead-schem.ru.error.log 2>/dev/null || echo "Лог ошибок пуст"
}

# Функция просмотра логов
view_logs() {
    log "📋 Просмотр логов..."
    
    echo "Выберите логи для просмотра:"
    echo "1) Backend API"
    echo "2) Frontend"
    echo "3) Nginx"
    echo "4) Все логи"
    read -p "Введите номер (1-4): " log_choice
    
    case $log_choice in
        1)
            docker logs leadschem_backend --tail=50
            ;;
        2)
            docker logs leadschem_frontend --tail=50
            ;;
        3)
            tail -50 /var/log/nginx/lead-schem.ru.access.log
            ;;
        4)
            log "=== Backend ==="
            docker logs leadschem_backend --tail=20
            log "=== Frontend ==="
            docker logs leadschem_frontend --tail=20
            log "=== Nginx ==="
            tail -20 /var/log/nginx/lead-schem.ru.access.log
            ;;
        *)
            error "Неверный выбор"
            ;;
    esac
}

# Функция перезапуска
restart_services() {
    log "♻️ Перезапуск сервисов..."
    
    cd $PROJECT_DIR/deployment
    docker-compose -f docker-compose.production.yml restart
    systemctl restart nginx
    
    log "✅ Сервисы перезапущены"
}

# Функция обновления
update_application() {
    log "🔄 Обновление приложения..."
    
    # Обновление кода
    cd $PROJECT_DIR
    git pull origin main || warn "Git pull failed"
    
    # Пересборка и перезапуск
    build_application
    deploy_application
    
    log "✅ Приложение обновлено"
}

# Функция backup
backup_database() {
    log "💾 Создание backup базы данных..."
    
    BACKUP_DIR="/opt/leadschem/backups"
    mkdir -p $BACKUP_DIR
    
    BACKUP_FILE="$BACKUP_DIR/leadschem_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Backup существующей базы данных (используем переменные из .env)
    source /opt/leadschem/.env
    PGPASSWORD="$POSTGRESQL_PASSWORD" pg_dump \
        -h "$POSTGRESQL_HOST" \
        -U "$POSTGRESQL_USER" \
        -d "$POSTGRESQL_DBNAME" \
        -f "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        log "✅ Backup создан: $BACKUP_FILE"
        
        # Сжатие backup
        gzip "$BACKUP_FILE"
        log "📦 Backup сжат: $BACKUP_FILE.gz"
        
        # Удаление старых backup (старше 7 дней)
        find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
        log "🧹 Старые backup удалены"
    else
        error "Ошибка создания backup"
    fi
}

# Основная логика
main() {
    if [ "$FULL_INSTALL" = true ]; then
        full_install
        clone_repository
        build_application
        deploy_application
        setup_ssl
        check_status
    elif [ "$DEPLOY_ONLY" = true ]; then
        clone_repository
        build_application
        deploy_application
    elif [ "$UPDATE_ONLY" = true ]; then
        update_application
    elif [ "$SSL_ONLY" = true ]; then
        setup_ssl
    elif [ "$RESTART_ONLY" = true ]; then
        restart_services
    elif [ "$STATUS_ONLY" = true ]; then
        check_status
    elif [ "$LOGS_ONLY" = true ]; then
        view_logs
    elif [ "$BACKUP_ONLY" = true ]; then
        backup_database
    fi
    
    log "🎉 Операция завершена!"
    
    if [ "$FULL_INSTALL" = true ] || [ "$DEPLOY_ONLY" = true ]; then
        echo ""
        log "📋 Полезная информация:"
        log "   🌐 Сайт: https://$DOMAIN"
        log "   📊 Мониторинг: https://$DOMAIN/monitoring"
        log "   📚 API документация: https://$DOMAIN/api/docs"
        log "   📁 Проект: $PROJECT_DIR"
        log "   📋 Статус: ./deploy.sh -> 6"
        log "   📋 Логи: ./deploy.sh -> 7"
        echo ""
        log "🔧 Управление:"
        log "   systemctl status leadschem    - Статус приложения"
        log "   systemctl restart leadschem   - Перезапуск приложения"
        log "   check-ssl                     - Проверка SSL"
    fi
}

# Запуск основной функции
main 