#!/bin/bash
# Скрипт настройки SSL для lead-schem.ru
# Запускать после базовой настройки сервера

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Проверка запуска от root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен от root"
fi

DOMAIN="lead-schem.ru"
WWW_DOMAIN="www.lead-schem.ru"
EMAIL="admin@lead-schem.ru"  # Замените на ваш email

log "🔒 Настройка SSL для домена $DOMAIN..."

# 1. Остановка Nginx (если запущен)
log "⏹️ Остановка Nginx..."
systemctl stop nginx || true

# 2. Создание базовой конфигурации Nginx для проверки домена
log "📝 Создание временной конфигурации Nginx..."
cat > /etc/nginx/sites-available/temp-ssl << EOF
server {
    listen 80;
    server_name $DOMAIN $WWW_DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 200 "SSL setup in progress...";
        add_header Content-Type text/plain;
    }
}
EOF

# Удаляем default конфигурацию и создаем симлинк
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/temp-ssl /etc/nginx/sites-enabled/

# 3. Создание директории для временных файлов
mkdir -p /var/www/html

# 4. Проверка конфигурации Nginx
log "🔍 Проверка конфигурации Nginx..."
nginx -t || error "Ошибка в конфигурации Nginx"

# 5. Запуск Nginx
log "▶️ Запуск Nginx..."
systemctl start nginx

# 6. Проверка доступности домена
log "🌐 Проверка доступности домена..."
if ! curl -s http://$DOMAIN > /dev/null; then
    warn "Домен $DOMAIN недоступен. Убедитесь, что DNS записи настроены правильно."
    warn "A запись должна указывать на 194.87.201.221"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 7. Получение SSL сертификата
log "📜 Получение SSL сертификата от Let's Encrypt..."
certbot certonly \
    --webroot \
    --webroot-path=/var/www/html \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN,$WWW_DOMAIN

if [ $? -ne 0 ]; then
    error "Не удалось получить SSL сертификат"
fi

# 8. Создание production конфигурации Nginx
log "📝 Создание production конфигурации Nginx..."
cp /opt/leadschem/deployment/nginx/lead-schem.ru.conf /etc/nginx/sites-available/lead-schem.ru

# Удаляем временную конфигурацию
rm -f /etc/nginx/sites-enabled/temp-ssl
ln -sf /etc/nginx/sites-available/lead-schem.ru /etc/nginx/sites-enabled/

# 9. Проверка новой конфигурации
log "🔍 Проверка production конфигурации..."
nginx -t || error "Ошибка в production конфигурации Nginx"

# 10. Перезагрузка Nginx
log "🔄 Перезагрузка Nginx..."
systemctl reload nginx

# 11. Настройка автоматического обновления сертификатов
log "🔄 Настройка автоматического обновления сертификатов..."
cat > /etc/cron.d/certbot-renew << EOF
# Обновление Let's Encrypt сертификатов
0 12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

# 12. Тест SSL конфигурации
log "🧪 Тестирование SSL конфигурации..."
sleep 5
if curl -s https://$DOMAIN > /dev/null; then
    log "✅ SSL успешно настроен!"
    log "🌐 Сайт доступен по адресу: https://$DOMAIN"
else
    warn "⚠️ SSL настроен, но сайт пока недоступен (возможно, приложение не запущено)"
fi

# 13. Создание скрипта проверки SSL
log "📋 Создание скрипта проверки SSL..."
cat > /usr/local/bin/check-ssl << 'EOF'
#!/bin/bash
echo "=== SSL Certificate Info ==="
certbot certificates
echo ""
echo "=== SSL Test ==="
curl -I https://lead-schem.ru 2>/dev/null | head -1
echo ""
echo "=== Certificate Expiry ==="
openssl x509 -in /etc/letsencrypt/live/lead-schem.ru/cert.pem -text -noout | grep "Not After"
EOF

chmod +x /usr/local/bin/check-ssl

log "🎉 SSL настройка завершена!"
log "📋 Полезные команды:"
log "   check-ssl                    - Проверка SSL сертификата"
log "   certbot renew --dry-run      - Тест обновления сертификата"
log "   systemctl reload nginx       - Перезагрузка Nginx"
log "   systemctl status nginx       - Статус Nginx"
log ""
log "🔒 SSL сертификат автоматически обновляется каждый день в 12:00"
log "🌐 Ваш сайт доступен по адресу: https://$DOMAIN" 