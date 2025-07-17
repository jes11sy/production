# 🚀 Руководство по развертыванию

## 📋 Системные требования

### Минимальные требования
- **OS:** Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **CPU:** 2 ядра, 2.0 GHz
- **RAM:** 4 GB
- **Disk:** 10 GB свободного места

### Рекомендуемые требования
- **CPU:** 4 ядра, 2.5 GHz
- **RAM:** 8 GB
- **Disk:** 20 GB SSD

### Необходимое ПО
- **Node.js:** 18.x или выше
- **Python:** 3.11 или выше
- **PostgreSQL:** 13.x или выше
- **Git:** Последняя версия

---

## 🔧 Локальная разработка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd project
```

### 2. Настройка backend

#### Установка зависимостей
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### Настройка базы данных
```bash
# Создание пользователя и базы данных PostgreSQL
createuser -s postgres
createdb -O postgres project_db

# Или через psql
psql -U postgres
CREATE DATABASE project_db;
CREATE USER project_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE project_db TO project_user;
```

#### Настройка переменных окружения
```bash
# backend/.env
SECRET_KEY=your-super-secret-key-here-min-32-chars
DATABASE_URL=postgresql://project_user:your_password@localhost/project_db
POSTGRESQL_USER=project_user
POSTGRESQL_PASSWORD=your_password
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=project_db

# CORS настройки
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Настройки файлов
MEDIA_ROOT=media/
MAX_FILE_SIZE=10485760  # 10MB
```

#### Миграции базы данных
```bash
# Создание миграций
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head
```

#### Создание администратора
```bash
python create_admin_simple.py
```

#### Запуск сервера разработки
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Настройка frontend

#### Установка зависимостей
```bash
cd frontend
npm install
```

#### Настройка переменных окружения
```bash
# frontend/.env.development
VITE_API_URL=http://localhost:8000/api/v1

# frontend/.env.production
VITE_API_URL=https://your-api-domain.com/api/v1
```

#### Запуск сервера разработки
```bash
npm run dev
```

### 4. Проверка работы
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## 🐳 Docker развертывание

### 1. Создание Docker файлов

#### backend/Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директории для media файлов
RUN mkdir -p media

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### frontend/Dockerfile
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./
RUN npm ci

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Production image
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=builder /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: project_db
      POSTGRES_USER: project_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      SECRET_KEY: your-super-secret-key-here-min-32-chars
      DATABASE_URL: postgresql://project_user:your_password@postgres/project_db
      POSTGRESQL_USER: project_user
      POSTGRESQL_PASSWORD: your_password
      POSTGRESQL_HOST: postgres
      POSTGRESQL_PORT: 5432
      POSTGRESQL_DATABASE: project_db
      CORS_ORIGINS: http://localhost:3000,http://localhost:5173
    depends_on:
      - postgres
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media

  frontend:
    build: 
      context: ./frontend
      args:
        VITE_API_URL: http://localhost:8000/api/v1
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 2. Запуск Docker контейнеров
```bash
# Сборка и запуск
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f backend
docker-compose logs -f frontend

# Остановка
docker-compose down
```

---

## 🌐 Production развертывание

### 1. Подготовка сервера

#### Установка зависимостей (Ubuntu)
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Установка Nginx
sudo apt install nginx -y

# Установка Python и pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# Установка Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Установка PM2
sudo npm install -g pm2
```

#### Настройка PostgreSQL
```bash
sudo -u postgres psql

CREATE DATABASE project_db;
CREATE USER project_user WITH PASSWORD 'secure_password';
ALTER USER project_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE project_db TO project_user;
\q
```

#### Настройка firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Деплой backend

#### Клонирование и настройка
```bash
cd /var/www
sudo git clone <repository-url> project
sudo chown -R $USER:$USER /var/www/project
cd project/backend

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Настройка переменных окружения
```bash
# /var/www/project/backend/.env
SECRET_KEY=your-super-secure-secret-key-for-production
DATABASE_URL=postgresql://project_user:secure_password@localhost/project_db
POSTGRESQL_USER=project_user
POSTGRESQL_PASSWORD=secure_password
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=project_db

# CORS настройки
CORS_ORIGINS=https://your-domain.com

# Настройки файлов
MEDIA_ROOT=/var/www/project/media/
MAX_FILE_SIZE=10485760

# Production настройки
ENVIRONMENT=production
DEBUG=false
```

#### Применение миграций
```bash
source venv/bin/activate
alembic upgrade head
python create_admin_simple.py
```

#### Настройка PM2
```bash
# ecosystem.config.js
module.exports = {
  apps: [{
    name: 'project-backend',
    script: 'venv/bin/uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 8000',
    cwd: '/var/www/project/backend',
    env: {
      NODE_ENV: 'production'
    }
  }]
};

# Запуск
pm2 start ecosystem.config.js
pm2 startup
pm2 save
```

### 3. Деплой frontend

#### Сборка
```bash
cd /var/www/project/frontend

# Настройка переменных окружения
echo "VITE_API_URL=https://your-domain.com/api/v1" > .env.production

# Установка зависимостей и сборка
npm install
npm run build
```

#### Настройка Nginx
```nginx
# /etc/nginx/sites-available/project
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/project/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Media files
    location /media/ {
        alias /var/www/project/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

#### Активация сайта
```bash
sudo ln -s /etc/nginx/sites-available/project /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL сертификат (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

---

## 🔐 Безопасность

### 1. Настройка HTTPS
```nginx
# Принудительное перенаправление на HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8000;
        # ... остальные настройки
    }
}
```

### 2. Настройка firewall
```bash
# Только необходимые порты
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw deny 8000  # Блокируем прямой доступ к backend
sudo ufw enable
```

### 3. Мониторинг
```bash
# Настройка логирования
sudo mkdir -p /var/log/project
sudo chown -R $USER:$USER /var/log/project

# Ротация логов
sudo nano /etc/logrotate.d/project
```

---

## 📊 Мониторинг и обслуживание

### 1. Проверка здоровья системы
```bash
# Статус сервисов
sudo systemctl status nginx
sudo systemctl status postgresql
pm2 status

# Логи
sudo tail -f /var/log/nginx/error.log
pm2 logs project-backend
sudo journalctl -u postgresql
```

### 2. Бэкапы
```bash
# Backup скрипт
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/project"

# Создание директории
mkdir -p $BACKUP_DIR

# Backup базы данных
pg_dump -U project_user -h localhost project_db > $BACKUP_DIR/db_$DATE.sql

# Backup media файлов
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/project/media

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 3. Автоматизация
```bash
# Добавление в crontab
crontab -e

# Ежедневный бэкап в 2:00
0 2 * * * /path/to/backup.sh

# Обновление SSL сертификата
0 3 * * * certbot renew --quiet
```

---

## 🚨 Troubleshooting

### Частые проблемы и решения

#### 1. Backend не запускается
```bash
# Проверка логов
pm2 logs project-backend

# Проверка зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Проверка БД подключения
psql -U project_user -h localhost project_db
```

#### 2. Frontend не загружается
```bash
# Проверка сборки
cd /var/www/project/frontend
npm run build

# Проверка Nginx
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. Проблемы с правами доступа
```bash
# Исправление прав
sudo chown -R www-data:www-data /var/www/project
sudo chmod -R 755 /var/www/project
```

#### 4. Проблемы с SSL
```bash
# Проверка сертификата
sudo certbot certificates

# Обновление сертификата
sudo certbot renew --dry-run
```

---

## 📋 Чек-лист деплоя

### Перед деплоем
- [ ] Протестировать локально
- [ ] Создать бэкап текущей версии
- [ ] Проверить все переменные окружения
- [ ] Убедиться что SECRET_KEY изменен
- [ ] Проверить CORS настройки

### После деплоя
- [ ] Проверить работу API
- [ ] Проверить работу frontend
- [ ] Проверить SSL сертификат
- [ ] Протестировать аутентификацию
- [ ] Проверить загрузку файлов
- [ ] Настроить мониторинг
- [ ] Настроить бэкапы

### Регулярное обслуживание
- [ ] Еженедельная проверка логов
- [ ] Ежемесячное обновление зависимостей
- [ ] Квартальный аудит безопасности
- [ ] Регулярное тестирование бэкапов 