#!/bin/bash

# =========================================
# 🚀 АВТОМАТИЧЕСКОЕ РАЗВЕРТЫВАНИЕ LEAD-SCHEM
# =========================================

set -e  # Выход при ошибке

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен от имени root (sudo)"
fi

# Параметры конфигурации
DOMAIN="lead-schem.ru"
PROJECT_DIR="/opt/leadschem"
REPO_URL="https://github.com/your-username/production.git"  # ИЗМЕНИТЬ НА ВАШ РЕПОЗИТОРИЙ!
DB_BACKUP_DIR="/opt/leadschem/backups"
NGINX_SITES_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"

# Параметры базы данных (будут заменены на значения из .env)
DB_HOST="74ac89b6f8cc981b84f28f3b.twc1.net"
DB_USER="gen_user" 
DB_NAME="default_db"

log "🚀 Начинаем автоматическое развертывание Lead Schema..."

# =========================================
# 1. ПОДГОТОВКА СИСТЕМЫ
# =========================================

install_system_dependencies() {
    log "📦 Установка системных зависимостей..."
    
    # Обновление системы
    apt update && apt upgrade -y
    
    # Установка основных пакетов
    apt install -y \
        curl \
        wget \
        git \
        unzip \
        nano \
        htop \
        ufw \
        fail2ban \
        certbot \
        python3-certbot-nginx \
        postgresql-client \
        nginx \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release

    log "✅ Системные зависимости установлены"
}

# =========================================
# 2. УСТАНОВКА DOCKER
# =========================================

install_docker() {
    log "🐳 Установка Docker..."
    
    # Удаление старых версий
    apt remove -y docker docker-engine docker.io containerd runc || true
    
    # Добавление официального GPG ключа Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Добавление репозитория Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Установка Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Добавление пользователя в группу docker
    usermod -aG docker $SUDO_USER || true
    
    # Запуск Docker
    systemctl enable docker
    systemctl start docker
    
    log "✅ Docker установлен и запущен"
}

# =========================================
# 3. НАСТРОЙКА ПРОЕКТА
# =========================================

setup_project() {
    log "📁 Настройка проекта..."
    
    # Создание директории проекта
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    
    # Клонирование репозитория
    if [ -d ".git" ]; then
        log "📥 Обновление существующего репозитория..."
        git pull origin main
    else
        log "📥 Клонирование репозитория..."
        git clone $REPO_URL .
    fi
    
    # Создание директорий
    mkdir -p {logs,media,backups,monitoring/data}
    
    # Установка прав доступа
    chown -R $SUDO_USER:$SUDO_USER $PROJECT_DIR
    chmod -R 755 $PROJECT_DIR
    
    log "✅ Проект настроен"
}

# =========================================
# 4. СОЗДАНИЕ .ENV ФАЙЛА
# =========================================

create_env_file() {
    log "⚙️ Создание .env файла..."
    
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log "📝 .env файл не найден, создаем новый..."
        
        # Генерация секретных ключей
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_SECRET_KEY=$(openssl rand -base64 32)
        CSRF_SECRET_KEY=$(openssl rand -hex 32)
        GRAFANA_PASSWORD=$(openssl rand -base64 16)
        
        cat > $PROJECT_DIR/.env << EOF
# =================================
# PRODUCTION CONFIGURATION
# =================================

# Режим работы
ENVIRONMENT=production
DEBUG=false
NODE_ENV=production

# Домен и URL
DOMAIN=$DOMAIN
FRONTEND_URL=https://$DOMAIN
BACKEND_URL=https://$DOMAIN/api/v1

# =================================
# БЕЗОПАСНОСТЬ
# =================================

# Секретные ключи (АВТОГЕНЕРИРОВАНЫ)
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
CSRF_SECRET_KEY=$CSRF_SECRET_KEY

# CORS настройки
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CORS_CREDENTIALS=true
ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

# =================================
# БАЗА ДАННЫХ
# =================================

# ВНИМАНИЕ: УКАЖИТЕ ВАШИ РЕАЛЬНЫЕ ДАННЫЕ!
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@$DB_HOST:5432/$DB_NAME
POSTGRESQL_HOST=$DB_HOST
POSTGRESQL_USER=YOUR_USER
POSTGRESQL_PASSWORD=YOUR_PASSWORD
POSTGRESQL_DBNAME=$DB_NAME
POSTGRESQL_PORT=5432

# Настройки пула подключений
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30

# =================================
# REDIS
# =================================

REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=
REDIS_SSL=false

# =================================
# ФАЙЛЫ И МЕДИА
# =================================

MEDIA_ROOT=/opt/leadschem/media/
MEDIA_URL=https://$DOMAIN/media/
MAX_FILE_SIZE=104857600

# =================================
# EMAIL (ОПЦИОНАЛЬНО)
# =================================

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_USE_TLS=true

# =================================
# МОНИТОРИНГ
# =================================

GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD
PROMETHEUS_ENABLED=true
METRICS_ENABLED=true

# =================================
# TELEGRAM АЛЕРТЫ (ОПЦИОНАЛЬНО)
# =================================

TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID

EOF
        
        warn "⚠️  ВАЖНО: Отредактируйте файл $PROJECT_DIR/.env"
        warn "⚠️  Укажите реальные данные подключения к базе данных!"
        warn "⚠️  Grafana пароль: $GRAFANA_PASSWORD"
        
        # Показываем что нужно изменить
        echo ""
        error "ОСТАНОВКА: Отредактируйте .env файл перед продолжением!"
        
    else
        log "✅ .env файл уже существует"
    fi
}

# =========================================
# 5. НАСТРОЙКА БАЗЫ ДАННЫХ
# =========================================

setup_database() {
    log "🗄️ Настройка базы данных..."
    
    # Загружаем переменные из .env
    source $PROJECT_DIR/.env
    
    if [ "$POSTGRESQL_PASSWORD" == "YOUR_PASSWORD" ]; then
        error "❌ Сначала настройте реальные данные БД в .env файле!"
    fi
    
    # Создание backup
    log "💾 Создание backup базы данных..."
    mkdir -p $DB_BACKUP_DIR
    
    BACKUP_FILE="$DB_BACKUP_DIR/pre_deploy_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    PGPASSWORD="$POSTGRESQL_PASSWORD" pg_dump \
        -h "$POSTGRESQL_HOST" \
        -U "$POSTGRESQL_USER" \
        -d "$POSTGRESQL_DBNAME" \
        -f "$BACKUP_FILE" && \
    gzip "$BACKUP_FILE" && \
    log "✅ Backup создан: ${BACKUP_FILE}.gz"
    
    log "✅ База данных настроена"
}

# =========================================
# 6. НАСТРОЙКА FIREWALL
# =========================================

setup_firewall() {
    log "🔥 Настройка firewall..."
    
    # Сброс правил
    ufw --force reset
    
    # Базовые правила
    ufw default deny incoming
    ufw default allow outgoing
    
    # Разрешенные порты
    ufw allow 22/tcp     # SSH
    ufw allow 80/tcp     # HTTP
    ufw allow 443/tcp    # HTTPS
    
    # Включение firewall
    ufw --force enable
    
    log "✅ Firewall настроен"
}

# =========================================
# 7. НАСТРОЙКА NGINX
# =========================================

setup_nginx() {
    log "🌐 Настройка Nginx..."
    
    # Копирование конфигурации
    cp $PROJECT_DIR/deployment/nginx/lead-schem.ru.conf $NGINX_SITES_DIR/
    
    # Включение сайта
    ln -sf $NGINX_SITES_DIR/lead-schem.ru.conf $NGINX_ENABLED_DIR/
    
    # Удаление дефолтного сайта
    rm -f $NGINX_ENABLED_DIR/default
    
    # Проверка конфигурации
    nginx -t || error "❌ Ошибка конфигурации Nginx"
    
    log "✅ Nginx настроен"
}

# =========================================
# 8. ПОЛУЧЕНИЕ SSL СЕРТИФИКАТОВ
# =========================================

setup_ssl() {
    log "🔒 Получение SSL сертификатов..."
    
    # Временный Nginx конфигурация для certbot
    cat > $NGINX_SITES_DIR/temp-$DOMAIN.conf << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
    
    ln -sf $NGINX_SITES_DIR/temp-$DOMAIN.conf $NGINX_ENABLED_DIR/
    systemctl reload nginx
    
    # Получение сертификата
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/html \
        --email admin@$DOMAIN \
        --agree-tos \
        --no-eff-email \
        --domains $DOMAIN,www.$DOMAIN
    
    # Удаление временной конфигурации
    rm -f $NGINX_ENABLED_DIR/temp-$DOMAIN.conf
    
    # Настройка автообновления
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
    
    log "✅ SSL сертификаты получены"
}

# =========================================
# 9. РАЗВЕРТЫВАНИЕ ПРИЛОЖЕНИЯ
# =========================================

deploy_application() {
    log "🚀 Развертывание приложения..."
    
    cd $PROJECT_DIR
    
    # Сборка и запуск контейнеров
    docker compose -f deployment/docker-compose.production.yml down || true
    docker compose -f deployment/docker-compose.production.yml pull
    docker compose -f deployment/docker-compose.production.yml build --no-cache
    docker compose -f deployment/docker-compose.production.yml up -d
    
    # Ожидание запуска
    log "⏳ Ожидание запуска сервисов..."
    sleep 30
    
    # Проверка статуса
    docker compose -f deployment/docker-compose.production.yml ps
    
    log "✅ Приложение развернуто"
}

# =========================================
# 10. НАСТРОЙКА МОНИТОРИНГА
# =========================================

setup_monitoring() {
    log "📊 Настройка мониторинга..."
    
    # Создание systemd сервиса для мониторинга
    cat > /etc/systemd/system/leadschem-monitoring.service << EOF
[Unit]
Description=Lead Schema Monitoring
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/docker compose -f $PROJECT_DIR/deployment/docker-compose.production.yml up -d prometheus grafana
WorkingDirectory=$PROJECT_DIR
User=root

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable leadschem-monitoring
    
    log "✅ Мониторинг настроен"
}

# =========================================
# 11. ФИНАЛЬНАЯ ПРОВЕРКА
# =========================================

final_check() {
    log "🔍 Финальная проверка системы..."
    
    sleep 10
    
    # Проверка сервисов
    echo ""
    echo "=== Статус Docker контейнеров ==="
    docker compose -f $PROJECT_DIR/deployment/docker-compose.production.yml ps
    
    echo ""
    echo "=== Статус Nginx ==="
    systemctl status nginx --no-pager -l
    
    echo ""
    echo "=== Проверка доступности ==="
    
    # Backend API
    if curl -s -k http://127.0.0.1:8000/health > /dev/null; then
        log "✅ Backend API доступен"
    else
        warn "❌ Backend API недоступен"
    fi
    
    # Frontend
    if curl -s -k http://127.0.0.1:3000 > /dev/null; then
        log "✅ Frontend доступен"
    else
        warn "❌ Frontend недоступен"
    fi
    
    # HTTPS сайт
    if curl -s -k https://$DOMAIN > /dev/null; then
        log "✅ Сайт доступен по HTTPS"
    else
        warn "❌ Сайт недоступен по HTTPS"
    fi
    
    echo ""
    log "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
    echo ""
    info "🌐 Сайт: https://$DOMAIN"
    info "📊 Мониторинг: https://$DOMAIN/monitoring/"
    info "📈 Метрики: https://$DOMAIN/metrics (только для админов)"
    info "📋 API Docs: https://$DOMAIN/docs"
    echo ""
    warn "⚠️  Не забудьте:"
    warn "   1. Настроить резервное копирование"
    warn "   2. Настроить Telegram алерты"
    warn "   3. Проверить все функции сайта"
    warn "   4. Создать админ пользователя"
    echo ""
}

# =========================================
# ГЛАВНАЯ ФУНКЦИЯ
# =========================================

main() {
    log "🚀 Запуск автоматического развертывания..."
    
    # Проверка аргументов
    if [ "$1" == "--skip-deps" ]; then
        log "⏭️ Пропускаем установку зависимостей"
    else
        install_system_dependencies
        install_docker
    fi
    
    setup_project
    create_env_file
    
    # Если .env файл был только что создан, останавливаемся
    if [ "$?" -ne 0 ]; then
        exit 1
    fi
    
    setup_database
    setup_firewall
    setup_nginx
    
    if [ "$1" != "--no-ssl" ]; then
        setup_ssl
    fi
    
    deploy_application
    setup_monitoring
    
    # Перезагрузка Nginx с окончательной конфигурацией
    systemctl restart nginx
    
    final_check
}

# =========================================
# ЗАПУСК
# =========================================

# Проверка аргументов
case "$1" in
    --help|-h)
        echo "Использование: $0 [опции]"
        echo ""
        echo "Опции:"
        echo "  --skip-deps    Пропустить установку системных зависимостей"
        echo "  --no-ssl       Пропустить настройку SSL"
        echo "  --help         Показать эту справку"
        echo ""
        echo "Пример:"
        echo "  sudo $0                 # Полное развертывание"
        echo "  sudo $0 --skip-deps    # Без установки зависимостей"
        echo "  sudo $0 --no-ssl       # Без SSL (для тестирования)"
        exit 0
        ;;
    *)
        main "$1"
        ;;
esac 