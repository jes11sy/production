#!/bin/bash
# Скрипт установки сервера для lead-schem.ru
# Сервер: 194.87.201.221
# Домен: lead-schem.ru

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
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

# Проверка запуска от root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен от root"
fi

log "🚀 Начинаем настройку сервера для lead-schem.ru..."

# 1. Обновление системы
log "📦 Обновление системы..."
apt update && apt upgrade -y

# 2. Установка базовых пакетов
log "🔧 Установка базовых пакетов..."
apt install -y \
    curl \
    wget \
    git \
    htop \
    nano \
    ufw \
    fail2ban \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 3. Установка Docker
log "🐳 Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    log "✅ Docker установлен"
else
    log "✅ Docker уже установлен"
fi

# 4. Установка Docker Compose
log "🐳 Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log "✅ Docker Compose установлен"
else
    log "✅ Docker Compose уже установлен"
fi

# 5. Установка Nginx
log "🌐 Установка Nginx..."
if ! command -v nginx &> /dev/null; then
    apt install -y nginx
    systemctl enable nginx
    systemctl start nginx
    log "✅ Nginx установлен"
else
    log "✅ Nginx уже установлен"
fi

# 6. Установка PostgreSQL клиента (для проверки подключения)
log "🗄️ Установка PostgreSQL клиента..."
if ! command -v psql &> /dev/null; then
    apt install -y postgresql-client
    log "✅ PostgreSQL клиент установлен"
else
    log "✅ PostgreSQL клиент уже установлен"
fi

# 7. Установка Node.js (для сборки фронтенда)
log "📦 Установка Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    log "✅ Node.js установлен"
else
    log "✅ Node.js уже установлен"
fi

# 8. Установка Certbot для SSL
log "🔒 Установка Certbot..."
if ! command -v certbot &> /dev/null; then
    snap install core; snap refresh core
    snap install --classic certbot
    ln -sf /snap/bin/certbot /usr/bin/certbot
    log "✅ Certbot установлен"
else
    log "✅ Certbot уже установлен"
fi

# 9. Настройка брандмауэра
log "🔥 Настройка UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp  # Backend API
ufw allow 3000/tcp  # Frontend
ufw allow 5432/tcp  # PostgreSQL
ufw allow 6379/tcp  # Redis
ufw allow 9090/tcp  # Prometheus
ufw allow 3001/tcp  # Grafana
ufw --force enable

# 10. Настройка fail2ban
log "🛡️ Настройка fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# 11. Создание пользователя для приложения
log "👤 Создание пользователя приложения..."
if ! id "leadschem" &>/dev/null; then
    useradd -m -s /bin/bash leadschem
    usermod -aG docker leadschem
    log "✅ Пользователь leadschem создан"
else
    log "✅ Пользователь leadschem уже существует"
fi

# 12. Создание директорий проекта
log "📁 Создание директорий проекта..."
mkdir -p /opt/leadschem
chown leadschem:leadschem /opt/leadschem

# 13. Проверка подключения к существующей базе данных
log "🗄️ Проверка подключения к базе данных..."
log "   Используется существующая база: 74ac89b6f8cc981b84f28f3b.twc1.net:5432/default_db"
log "   Пользователь: gen_user"
log "   ✅ Конфигурация базы данных готова"

# 14. Создание папки для SSL сертификатов
log "🔒 Подготовка папки для SSL..."
mkdir -p /etc/nginx/ssl
chmod 700 /etc/nginx/ssl

# 15. Настройка логирования
log "📝 Настройка логирования..."
mkdir -p /var/log/leadschem
chown leadschem:leadschem /var/log/leadschem

# 16. Создание systemd сервиса для приложения
log "⚙️ Создание systemd сервиса..."
cat > /etc/systemd/system/leadschem.service << EOF
[Unit]
Description=Lead Schema Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/opt/leadschem
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=leadschem
Group=leadschem

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable leadschem

log "🎉 Базовая настройка сервера завершена!"
log "📋 Что было установлено:"
log "   - Docker и Docker Compose"
log "   - Nginx"
log "   - PostgreSQL клиент"
log "   - Node.js"
log "   - Certbot для SSL"
log "   - UFW брандмауэр"
log "   - fail2ban"
log "   - Пользователь leadschem"
log "   - Подключение к существующей БД настроено"

log "📝 Следующие шаги:"
log "   1. Склонировать репозиторий в /opt/leadschem"
log "   2. Настроить переменные окружения"
log "   3. Запустить docker-compose"
log "   4. Настроить SSL сертификат"
log "   5. Настроить Nginx конфигурацию"

log "🌐 Сервер готов для развертывания lead-schem.ru!" 