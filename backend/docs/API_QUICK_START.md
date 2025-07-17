# 🚀 API Quick Start Guide

## Быстрый старт с интерактивной документацией

### 1. Запуск сервера

```bash
cd backend

# HTTP запуск (development)
python run.py

# HTTPS запуск (рекомендуется)
python run_https.py
```

### 2. Открытие документации

**Swagger UI (интерактивная документация):**
```
# HTTP
http://localhost:8000/docs

# HTTPS (рекомендуется)
https://localhost:8443/docs
```

**ReDoc (альтернативный интерфейс):**
```
# HTTP
http://localhost:8000/redoc

# HTTPS (рекомендуется)
https://localhost:8443/redoc
```

### 3. Тестирование API

#### Через Swagger UI:
1. Откройте https://localhost:8443/docs
2. Найдите эндпоинт `/api/v1/auth/login`
3. Нажмите "Try it out"
4. Введите данные для входа:
   ```json
   {
     "login": "master001",
     "password": "password123"
   }
   ```
5. Нажмите "Execute"
6. Токен автоматически сохранится для других запросов

#### Через демонстрационный скрипт:
```bash
# Полная демонстрация
python demo_api.py

# Только аутентификация
python demo_api.py --section auth

# Только API заявок
python demo_api.py --section requests

# Тестирование безопасности файлов
python demo_api.py --section security
```

## 🔐 Безопасные эндпоинты

### Безопасная работа с файлами

```bash
# Загрузка файла
curl -X POST "https://localhost:8443/api/v1/files/upload-expense-receipt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@receipt.jpg"

# Безопасная загрузка файла
curl -X GET "https://localhost:8443/api/v1/secure-files/download/zayvka/rashod/filename.jpg" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded_file.jpg

# Безопасный просмотр файла
curl -X GET "https://localhost:8443/api/v1/secure-files/view/zayvka/rashod/filename.jpg" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Примеры использования с JavaScript

```javascript
// Безопасная загрузка файла
const downloadFile = async (filePath) => {
  const response = await fetch(`https://localhost:8443/api/v1/secure-files/download/${filePath}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  
  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filePath.split('/').pop();
    a.click();
  }
};

// Безопасный просмотр файла
const viewFile = async (filePath) => {
  const response = await fetch(`https://localhost:8443/api/v1/secure-files/view/${filePath}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  
  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
  }
};
```

## 📊 Метрики с Redis кешированием

### Получение метрик

```bash
# Метрики заявок (кешированные)
curl -X GET "https://localhost:8443/api/v1/metrics/requests" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Метрики транзакций (кешированные)
curl -X GET "https://localhost:8443/api/v1/metrics/transactions" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Метрики пользователей (кешированные)
curl -X GET "https://localhost:8443/api/v1/metrics/users" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Статистика Redis (только для админов)
curl -X GET "https://localhost:8443/api/v1/admin/redis/stats" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Примеры ответов

```json
// Пример ответа метрик заявок
{
  "total_requests": 1250,
  "requests_by_status": {
    "pending": 45,
    "in_progress": 120,
    "completed": 980,
    "cancelled": 105
  },
  "requests_by_month": [
    {"month": "2024-01", "count": 150},
    {"month": "2024-02", "count": 200}
  ],
  "cache_info": {
    "cached": true,
    "ttl": 300,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}

// Пример ответа статистики Redis
{
  "cache_stats": {
    "hit_rate": 99.02,
    "hits": 2450,
    "misses": 24,
    "total_requests": 2474,
    "memory_usage": "2.5MB"
  },
  "redis_info": {
    "connected_clients": 5,
    "used_memory": 2621440,
    "used_memory_human": "2.50M",
    "keyspace_hits": 2450,
    "keyspace_misses": 24
  }
}
```

## 🛡️ Примеры безопасности

### Контроль доступа к файлам

```python
# Python пример с проверкой ролей
import httpx

async def access_file_by_role(token: str, file_path: str):
    """Доступ к файлу с проверкой роли"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(
            f"https://localhost:8443/api/v1/secure-files/view/{file_path}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.content
        elif response.status_code == 403:
            print("Доступ запрещен: недостаточно прав")
        elif response.status_code == 404:
            print("Файл не найден")
        else:
            print(f"Ошибка: {response.status_code}")
    
    return None

# Использование
# admin_token - полный доступ ко всем файлам
# master_token - доступ только к файлам своих заявок
```

### HTTPS клиент для Python

```python
import httpx
import ssl

# Создание SSL контекста для самоподписанных сертификатов
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def make_secure_request(endpoint: str, token: str):
    """Безопасный запрос к API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(verify=ssl_context) as client:
        response = await client.get(
            f"https://localhost:8443{endpoint}",
            headers=headers
        )
        return response.json()

# Примеры использования
# await make_secure_request("/api/v1/metrics/requests", token)
# await make_secure_request("/api/v1/secure-files/view/file.jpg", token)
```

## 🔧 Настройка среды разработки

### Переменные окружения

```env
# Обязательные настройки
SECRET_KEY=your-64-character-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379

# HTTPS настройки
SSL_CERT_PATH=./ssl/cert.pem
SSL_KEY_PATH=./ssl/key.pem

# Дополнительные настройки
ENVIRONMENT=development
ALLOWED_ORIGINS=https://localhost:3000,https://localhost:5173
```

### Проверка подключений

```bash
# Проверка базы данных
python scripts/check_db.py

# Проверка Redis
redis-cli ping

# Проверка SSL сертификатов
openssl x509 -in ssl/cert.pem -text -noout

# Тест API
curl -k https://localhost:8443/api/v1/health
```

## 🚨 Устранение неполадок

### Частые проблемы

1. **SSL сертификат не найден**
   ```bash
   # Создание нового сертификата
   python -c "from app.ssl_config import create_ssl_context; create_ssl_context()"
   ```

2. **Redis не подключается**
   ```bash
   # Проверка статуса Redis
   redis-cli ping
   
   # Запуск Redis (Windows)
   redis-server
   ```

3. **Проблемы с правами доступа к файлам**
   ```bash
   # Проверка структуры папок
   ls -la media/
   
   # Создание недостающих папок
   mkdir -p media/zayvka/rashod
   mkdir -p media/zayvka/bso
   ```

### Логи и отладка

```bash
# Просмотр логов приложения
tail -f app.log

# Мониторинг Redis
redis-cli monitor

# Проверка метрик производительности
curl -k https://localhost:8443/api/v1/admin/redis/stats
```

## 📚 Дополнительные ресурсы

- [Полная API документация](API_DOCUMENTATION_INTERACTIVE.md)
- [Руководство по безопасности](SECURITY_GUIDE.md)
- [Redis интеграция](REDIS_INTEGRATION.md)
- [Мониторинг системы](MONITORING.md)

## 🎯 Следующие шаги

1. **Изучите интерактивную документацию** в Swagger UI
2. **Протестируйте безопасные эндпоинты** с разными ролями
3. **Настройте HTTPS** для production среды
4. **Мониторьте производительность** через Redis метрики
5. **Изучите систему уведомлений** во frontend 