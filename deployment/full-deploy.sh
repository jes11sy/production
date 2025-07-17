#!/bin/bash

# =============================================================================
# Скрипт полного деплоя проекта LeadSchem Production
# =============================================================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Автоматическая установка Docker
install_docker() {
    print_step "Установка Docker и Docker Compose..."
    
    # Обновление системы
    apt update
    apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Добавление официального GPG ключа Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Добавление репозитория Docker
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Установка Docker Engine
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    
    # Установка Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Запуск Docker
    systemctl start docker
    systemctl enable docker
    
    print_success "Docker и Docker Compose успешно установлены!"
}

# Проверка и создание .env файла
setup_environment() {
    print_step "Настройка переменных окружения..."
    
    if [ ! -f "env.production.lead-schem" ]; then
        print_warning "Файл env.production.lead-schem не найден!"
        print_step "Создаю базовый файл конфигурации..."
        
        cat > env.production.lead-schem << 'EOF'
# База данных PostgreSQL
DATABASE_URL=postgresql://leadschem_user:strong_password_here@localhost:5432/leadschem_db
POSTGRESQL_HOST=localhost
POSTGRESQL_USER=leadschem_user
POSTGRESQL_PASSWORD=strong_password_here
POSTGRESQL_DBNAME=leadschem_db
POSTGRESQL_PORT=5432

# Безопасность
SECRET_KEY=your_very_long_secret_key_here_change_this_in_production
JWT_SECRET_KEY=your_jwt_secret_key_here_change_this_too
DEBUG=false

# CORS настройки
BACKEND_CORS_ORIGINS=https://lead-schem.ru,https://www.lead-schem.ru
ALLOWED_ORIGINS=https://lead-schem.ru,https://www.lead-schem.ru
CORS_ORIGINS=https://lead-schem.ru,https://www.lead-schem.ru
ALLOWED_HOSTS=lead-schem.ru,www.lead-schem.ru,localhost,127.0.0.1

# Файлы
MAX_FILE_SIZE=104857600
ALLOWED_FILE_TYPES=pdf,doc,docx,txt,jpg,jpeg,png,gif
UPLOAD_DIR=media
MAX_FILES_PER_USER=100

# Безопасность
RATE_LIMIT_PER_MINUTE=100
LOGIN_ATTEMPTS_PER_HOUR=5

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_USE_TLS=true

# Grafana
GRAFANA_ADMIN_PASSWORD=strong_grafana_password_here
EOF
        
        print_warning "❗ ВАЖНО: Отредактируйте файл env.production.lead-schem и установите правильные пароли и ключи!"
        print_warning "Особенно важно изменить:"
        print_warning "- POSTGRESQL_PASSWORD"
        print_warning "- SECRET_KEY"
        print_warning "- JWT_SECRET_KEY"
        print_warning "- GRAFANA_ADMIN_PASSWORD"
        print_warning "- SMTP_USER и SMTP_PASSWORD"
        
        read -p "Нажмите Enter после редактирования файла env.production.lead-schem..."
    fi
    
    print_success "Файл конфигурации готов"
}

# Проверка системных требований
check_requirements() {
    print_step "Проверка системных требований..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker не установлен! Автоматически устанавливаю..."
        install_docker
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_warning "Docker Compose не установлен! Автоматически устанавливаю..."
        install_docker
    fi
    
    # Проверка доступности портов
    ports=(80 443 3000 8000 6379 9090 3001)
    for port in "${ports[@]}"; do
        if netstat -tuln | grep ":$port " > /dev/null; then
            print_warning "Порт $port уже используется. Возможны конфликты."
        fi
    done
    
    print_success "Системные требования проверены"
}

# Подготовка директорий
prepare_directories() {
    print_step "Подготовка директорий..."
    
    # Создание необходимых директорий
    mkdir -p ../media
    mkdir -p ../logs
    mkdir -p ./nginx
    
    # Установка прав
    chmod 755 ../media
    chmod 755 ../logs
    
    print_success "Директории подготовлены"
}

# Создание конфигурации Nginx
setup_nginx() {
    print_step "Настройка Nginx конфигурации..."
    
    cat > ./nginx/lead-schem.ru.conf << 'EOF'
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

upstream grafana {
    server grafana:3000;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name lead-schem.ru www.lead-schem.ru;
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name lead-schem.ru www.lead-schem.ru;

    # SSL certificates (укажите правильные пути)
    ssl_certificate /etc/letsencrypt/live/lead-schem.ru/fullchain.pem;
    ssl_private_key /etc/letsencrypt/live/lead-schem.ru/privkey.pem;

    # SSL settings
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Client upload size
    client_max_body_size 100M;

    # API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Monitoring routes
    location /monitoring/ {
        proxy_pass http://grafana/;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files and frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Media files
    location /media/ {
        alias /var/www/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    print_success "Конфигурация Nginx создана"
}

# Сборка образов
build_images() {
    print_step "Сборка Docker образов..."
    
    # Остановка существующих контейнеров
    docker-compose -f docker-compose.production.yml down || true
    
    # Сборка образов
    docker-compose -f docker-compose.production.yml build --no-cache
    
    print_success "Docker образы собраны"
}

# Запуск сервисов
start_services() {
    print_step "Запуск сервисов..."
    
    # Запуск с переменными окружения
    docker-compose -f docker-compose.production.yml --env-file env.production.lead-schem up -d
    
    print_success "Сервисы запущены"
}

# Проверка здоровья сервисов
check_health() {
    print_step "Проверка работоспособности сервисов..."
    
    # Ожидание запуска
    sleep 30
    
    # Проверка каждого сервиса
    services=("redis" "backend" "frontend" "prometheus" "grafana" "nginx-proxy")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.production.yml ps "$service" | grep -q "Up"; then
            print_success "Сервис $service запущен"
        else
            print_error "Проблема с сервисом $service"
            docker-compose -f docker-compose.production.yml logs "$service" --tail=20
        fi
    done
    
    # Проверка HTTP ответов
    print_step "Проверка HTTP endpoints..."
    
    endpoints=(
        "http://localhost:8000/health|Backend Health"
        "http://localhost:3000|Frontend"
        "http://localhost:9090|Prometheus"
        "http://localhost:3001|Grafana"
    )
    
    for endpoint in "${endpoints[@]}"; do
        IFS='|' read -r url description <<< "$endpoint"
        if curl -f -s "$url" > /dev/null; then
            print_success "$description доступен"
        else
            print_warning "$description недоступен ($url)"
        fi
    done
}

# Настройка базы данных
setup_database() {
    print_step "Настройка базы данных..."
    
    # Ожидание готовности backend
    sleep 15
    
    # Выполнение миграций
    docker-compose -f docker-compose.production.yml exec backend python -m alembic upgrade head || true
    
    print_success "База данных настроена"
}

# Создание администратора
create_admin() {
    print_step "Создание администратора..."
    
    # Скрипт для создания админа внутри контейнера
    docker-compose -f docker-compose.production.yml exec backend python << 'EOF' || true
import asyncio
from app.core.database import get_db_session
from app.core.crud import create_user
from app.core.schemas import UserCreate
from app.core.security import get_password_hash

async def create_admin_user():
    async with get_db_session() as db:
        admin_user = UserCreate(
            username="admin",
            email="admin@lead-schem.ru",
            password="admin123",  # Измените пароль!
            is_superuser=True
        )
        try:
            await create_user(db, admin_user)
            print("✅ Администратор создан: admin / admin123")
            print("⚠️  ВАЖНО: Смените пароль после первого входа!")
        except Exception as e:
            print(f"ℹ️  Администратор уже существует или ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
EOF

    print_success "Администратор настроен"
}

# Показ информации о деплое
show_deploy_info() {
    print_step "Информация о развертывании:"
    echo ""
    echo "🌐 Веб-интерфейс:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "📊 Мониторинг:"
    echo "   Prometheus: http://localhost:9090"
    echo "   Grafana: http://localhost:3001 (admin / пароль из env файла)"
    echo ""
    echo "🔧 Управление:"
    echo "   Логи: docker-compose -f docker-compose.production.yml logs -f"
    echo "   Остановка: docker-compose -f docker-compose.production.yml down"
    echo "   Перезапуск: docker-compose -f docker-compose.production.yml restart"
    echo ""
    echo "👤 Администратор:"
    echo "   Логин: admin"
    echo "   Пароль: admin123 (ОБЯЗАТЕЛЬНО СМЕНИТЕ!)"
    echo ""
    print_warning "Не забудьте настроить SSL сертификаты для продакшена!"
    print_warning "Используйте: sudo certbot --nginx -d lead-schem.ru -d www.lead-schem.ru"
}

# Резервное копирование
backup_current() {
    print_step "Создание резервной копии текущего состояния..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_dir="backup_${timestamp}"
    
    mkdir -p "../$backup_dir"
    
    # Копирование важных файлов
    cp -r ../media "../$backup_dir/" 2>/dev/null || true
    cp -r ../logs "../$backup_dir/" 2>/dev/null || true
    cp env.production.lead-schem "../$backup_dir/" 2>/dev/null || true
    
    print_success "Резервная копия создана в ../$backup_dir"
}

# Основная функция
main() {
    echo "=================================================="
    echo "🚀 ПОЛНЫЙ ДЕПЛОЙ LEADSCHEM PRODUCTION"
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
    backup_current
    check_requirements
    setup_environment
    prepare_directories
    setup_nginx
    build_images
    start_services
    setup_database
    create_admin
    check_health
    show_deploy_info
    
    echo ""
    echo "=================================================="
    print_success "🎉 ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!"
    echo "=================================================="
}

# Обработка ошибок
trap 'echo -e "\n${RED}❌ Деплой прерван из-за ошибки!${NC}"' ERR

# Запуск основной функции
main "$@" 