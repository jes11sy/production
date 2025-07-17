# 🚀 Интерактивная документация API

## Обзор

Система управления заявками предоставляет REST API для работы с заявками, транзакциями и пользователями. API построен на FastAPI с автоматической генерацией документации.

## 🔗 Доступ к документации

### Swagger UI (рекомендуется)
```
http://localhost:8000/docs
```
Интерактивная документация с возможностью тестирования API прямо в браузере.

### ReDoc
```
http://localhost:8000/redoc
```
Альтернативный интерфейс документации с удобной навигацией.

### OpenAPI Schema
```
http://localhost:8000/openapi.json
```
Машиночитаемая схема API в формате OpenAPI 3.0.

## 🔐 Аутентификация

API использует JWT токены, передаваемые через httpOnly cookies для безопасности.

### Процесс аутентификации

1. **Вход в систему**
   ```bash
   POST /api/v1/auth/login
   Content-Type: application/json
   
   {
     "login": "master001",
     "password": "secure_password123"
   }
   ```

2. **Получение токена**
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "user_type": "master",
     "role": "master",
     "user_id": 1,
     "city_id": 1
   }
   ```

3. **Использование токена**
   Токен автоматически сохраняется в httpOnly cookie и используется для всех последующих запросов.

### Типы пользователей и роли

| Роль | Описание | Доступ |
|------|----------|---------|
| `master` | Мастер | Свои заявки и транзакции |
| `callcenter` | Колл-центр | Обработка заявок |
| `manager` | Менеджер | Управление пользователями |
| `director` | Директор | Отчеты и аналитика |
| `admin` | Администратор | Полный доступ |

## 📋 Основные эндпоинты

### 🔐 Аутентификация

#### POST /api/v1/auth/login
Вход в систему с получением JWT токена.

**Примеры запросов:**

```javascript
// Вход мастера
{
  "login": "master001",
  "password": "secure_password123"
}

// Вход сотрудника колл-центра
{
  "login": "callcenter_user",
  "password": "employee_pass456"
}

// Вход администратора
{
  "login": "admin",
  "password": "admin_secure789"
}
```

#### GET /api/v1/auth/me
Получение информации о текущем пользователе.

**Пример ответа:**
```json
{
  "id": 1,
  "login": "master001",
  "status": "active",
  "user_type": "master",
  "role": "master",
  "city_id": 1
}
```

#### POST /api/v1/auth/logout
Выход из системы (удаление токена).

### 📞 Заявки

#### POST /api/v1/requests/
Создание новой заявки.

**Полный пример:**
```json
{
  "city_id": 1,
  "request_type_id": 1,
  "client_phone": "+7 (999) 123-45-67",
  "client_name": "Иванов Иван Иванович",
  "address": "г. Москва, ул. Примерная, д. 123, кв. 45",
  "meeting_date": "2025-01-20T14:30:00",
  "direction_id": 1,
  "problem": "Не работает кондиционер, требуется диагностика",
  "status": "new",
  "advertising_campaign_id": 1,
  "ats_number": "ATS-2025-001",
  "call_center_name": "Петрова Анна",
  "call_center_notes": "Клиент очень вежливый, просит перезвонить после 15:00"
}
```

**Минимальный пример:**
```json
{
  "city_id": 1,
  "request_type_id": 2,
  "client_phone": "+7 (999) 987-65-43",
  "client_name": "Петров Петр"
}
```

#### GET /api/v1/requests/
Получение списка заявок с пагинацией.

**Параметры:**
- `skip` (int): Количество пропускаемых записей (по умолчанию: 0)
- `limit` (int): Максимальное количество записей (по умолчанию: 100, максимум: 1000)

**Пример запроса:**
```
GET /api/v1/requests/?skip=0&limit=50
```

#### GET /api/v1/requests/{request_id}
Получение информации о конкретной заявке.

**Пример ответа:**
```json
{
  "id": 1,
  "city_id": 1,
  "request_type_id": 1,
  "client_phone": "+7 (999) 123-45-67",
  "client_name": "Иванов Иван Иванович",
  "address": "г. Москва, ул. Примерная, д. 123, кв. 45",
  "meeting_date": "2025-01-20T14:30:00",
  "status": "new",
  "created_at": "2025-01-15T10:30:00",
  "city": {
    "id": 1,
    "name": "Москва"
  },
  "request_type": {
    "id": 1,
    "name": "Ремонт кондиционера"
  },
  "master": {
    "id": 1,
    "full_name": "Сидоров Алексей Владимирович",
    "phone_number": "+7 (999) 555-12-34"
  },
  "files": []
}
```

#### PUT /api/v1/requests/{request_id}
Обновление заявки.

**Пример обновления мастером:**
```json
{
  "status": "completed",
  "master_notes": "Заменен фильтр кондиционера, проведена чистка",
  "result": 2500.00,
  "expenses": 450.00,
  "net_amount": 2050.00,
  "master_handover": 1230.00
}
```

**Пример назначения мастера:**
```json
{
  "status": "assigned",
  "master_id": 1,
  "master_notes": "Заявка назначена на завтра"
}
```

#### DELETE /api/v1/requests/{request_id}
Удаление заявки (только для администраторов).

### 💰 Транзакции

#### POST /api/v1/transactions/
Создание новой транзакции.

**Пример расходной операции:**
```json
{
  "city_id": 1,
  "transaction_type_id": 1,
  "amount": 15000.50,
  "notes": "Закупка запчастей для ремонта кондиционеров",
  "specified_date": "2025-01-15",
  "payment_reason": "Материалы для заявки #123"
}
```

**Пример зарплатной операции:**
```json
{
  "city_id": 1,
  "transaction_type_id": 2,
  "amount": 5000.00,
  "notes": "Оплата услуг мастера",
  "specified_date": "2025-01-15",
  "payment_reason": "Заработная плата"
}
```

#### GET /api/v1/transactions/
Получение списка транзакций с пагинацией.

#### GET /api/v1/transactions/{transaction_id}
Получение информации о конкретной транзакции.

#### PUT /api/v1/transactions/{transaction_id}
Обновление транзакции.

#### DELETE /api/v1/transactions/{transaction_id}
Удаление транзакции.

### 👥 Пользователи

#### POST /api/v1/users/masters/
Создание нового мастера.

**Пример:**
```json
{
  "city_id": 1,
  "full_name": "Сидоров Алексей Владимирович",
  "phone_number": "+7 (999) 555-12-34",
  "birth_date": "1985-03-15",
  "passport": "4510 123456",
  "login": "master_sidorov",
  "password": "secure_pass123",
  "chat_id": "telegram_123456789",
  "notes": "Специализация: кондиционеры, стаж 8 лет"
}
```

#### POST /api/v1/users/employees/
Создание нового сотрудника.

**Пример:**
```json
{
  "name": "Козлова Мария Петровна",
  "role_id": 2,
  "city_id": 1,
  "login": "maria_kozlova",
  "password": "employee_pass456",
  "notes": "Опыт работы в колл-центре 3 года"
}
```

#### GET /api/v1/users/masters/
Получение списка мастеров.

#### GET /api/v1/users/employees/
Получение списка сотрудников.

#### GET /api/v1/users/administrators/
Получение списка администраторов.

### 📁 Файлы

#### POST /api/v1/files/upload/{request_id}
Загрузка файла к заявке.

**Поддерживаемые форматы:**
- Изображения: JPG, JPEG, PNG
- Документы: PDF, DOC, DOCX
- Максимальный размер: 10MB

**Пример использования:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/v1/files/upload/123', {
  method: 'POST',
  body: formData
});
```

#### GET /api/v1/files/{file_path}
Получение файла по пути.

#### DELETE /api/v1/files/{file_id}
Удаление файла.

### ❤️ Мониторинг

#### GET /api/v1/health/
Базовая проверка здоровья системы.

**Пример ответа:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T15:00:00Z",
  "service": "Request Management System",
  "version": "1.0.0"
}
```

#### GET /api/v1/health/detailed
Детальная проверка всех компонентов системы.

**Пример ответа:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T15:00:00Z",
  "service": "Request Management System",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "details": "Connection pool: 8/10 active"
    },
    "file_storage": {
      "status": "healthy",
      "response_time_ms": 5,
      "details": "Disk space: 85% used"
    },
    "external_services": {
      "status": "healthy",
      "response_time_ms": 150,
      "details": "Mango Office API: OK"
    }
  }
}
```

### 🗄️ База данных

#### GET /api/v1/database/statistics
Получение статистики базы данных (только для администраторов).

#### GET /api/v1/database/optimization-report
Отчет по оптимизации базы данных.

#### POST /api/v1/database/optimize
Запуск оптимизации базы данных.

## 🔧 Коды ответов

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 201 | Ресурс успешно создан |
| 400 | Некорректные данные запроса |
| 401 | Требуется аутентификация |
| 403 | Недостаточно прав доступа |
| 404 | Ресурс не найден |
| 422 | Ошибка валидации данных |
| 429 | Превышен лимит запросов |
| 500 | Внутренняя ошибка сервера |

## 🛠️ Примеры использования

### JavaScript/TypeScript

```javascript
// Класс для работы с API
class ApiClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async login(login, password) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Важно для cookies
      body: JSON.stringify({ login, password })
    });
    
    if (!response.ok) {
      throw new Error('Login failed');
    }
    
    return response.json();
  }

  async getRequests(skip = 0, limit = 100) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/requests/?skip=${skip}&limit=${limit}`,
      {
        credentials: 'include'
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch requests');
    }
    
    return response.json();
  }

  async createRequest(requestData) {
    const response = await fetch(`${this.baseUrl}/api/v1/requests/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(requestData)
    });
    
    if (!response.ok) {
      throw new Error('Failed to create request');
    }
    
    return response.json();
  }
}

// Использование
const api = new ApiClient();

// Вход в систему
await api.login('master001', 'password123');

// Получение заявок
const requests = await api.getRequests();

// Создание заявки
const newRequest = await api.createRequest({
  city_id: 1,
  request_type_id: 1,
  client_phone: '+7 (999) 123-45-67',
  client_name: 'Иванов Иван'
});
```

### Python

```python
import requests
import json

class ApiClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, login, password):
        response = self.session.post(
            f'{self.base_url}/api/v1/auth/login',
            json={'login': login, 'password': password}
        )
        response.raise_for_status()
        return response.json()
    
    def get_requests(self, skip=0, limit=100):
        response = self.session.get(
            f'{self.base_url}/api/v1/requests/',
            params={'skip': skip, 'limit': limit}
        )
        response.raise_for_status()
        return response.json()
    
    def create_request(self, request_data):
        response = self.session.post(
            f'{self.base_url}/api/v1/requests/',
            json=request_data
        )
        response.raise_for_status()
        return response.json()

# Использование
api = ApiClient()

# Вход в систему
api.login('master001', 'password123')

# Получение заявок
requests = api.get_requests()

# Создание заявки
new_request = api.create_request({
    'city_id': 1,
    'request_type_id': 1,
    'client_phone': '+7 (999) 123-45-67',
    'client_name': 'Иванов Иван'
})
```

### cURL

```bash
# Вход в систему
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"login": "master001", "password": "password123"}' \
  -c cookies.txt

# Получение заявок
curl -X GET "http://localhost:8000/api/v1/requests/?skip=0&limit=10" \
  -b cookies.txt

# Создание заявки
curl -X POST "http://localhost:8000/api/v1/requests/" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "city_id": 1,
    "request_type_id": 1,
    "client_phone": "+7 (999) 123-45-67",
    "client_name": "Иванов Иван"
  }'
```

## 🔍 Тестирование API

### Использование Swagger UI

1. Откройте http://localhost:8000/docs
2. Нажмите "Authorize" в правом верхнем углу
3. Выполните вход через эндпоинт `/api/v1/auth/login`
4. Токен автоматически сохранится в cookies
5. Тестируйте любые эндпоинты прямо в браузере

### Postman Collection

Создайте коллекцию Postman с следующими настройками:

1. **Variables:**
   - `base_url`: `http://localhost:8000`

2. **Authentication:**
   - Type: Bearer Token
   - Token: `{{auth_token}}`

3. **Pre-request Script для login:**
   ```javascript
   pm.test("Login successful", function () {
     pm.response.to.have.status(200);
     const responseJson = pm.response.json();
     pm.collectionVariables.set("auth_token", responseJson.access_token);
   });
   ```

## 📊 Мониторинг и метрики

### Endpoints для мониторинга

- `/api/v1/health/` - Базовая проверка
- `/api/v1/health/detailed` - Детальная проверка
- `/api/v1/health/database` - Проверка базы данных
- `/api/v1/health/services` - Проверка внешних сервисов
- `/api/v1/database/statistics` - Статистика БД

### Логирование

Все запросы логируются с информацией:
- Время выполнения
- Статус ответа
- IP адрес клиента
- User-Agent
- Размер ответа

## 🚀 Развертывание

### Локальная разработка

```bash
# Установка зависимостей
cd backend
pip install -r requirements.txt

# Запуск сервера разработки
python run_dev.py

# Или через uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Продакшн

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск с Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📝 Changelog

### v1.0.0
- ✅ Интерактивная документация API
- ✅ Расширенные примеры для всех эндпоинтов
- ✅ Улучшенные схемы валидации
- ✅ Детальные описания ошибок
- ✅ Примеры использования на разных языках
- ✅ Мониторинг и метрики

## 🤝 Поддержка

Для получения помощи:
1. Изучите интерактивную документацию: http://localhost:8000/docs
2. Проверьте примеры в этом файле
3. Используйте эндпоинты мониторинга для диагностики
4. Проверьте логи приложения

## 📋 TODO

- [ ] Добавить WebSocket endpoints для реального времени
- [ ] Создать SDK для популярных языков
- [ ] Добавить GraphQL endpoint
- [ ] Расширить систему ролей и разрешений
- [ ] Добавить rate limiting по пользователям
- [ ] Создать систему версионирования API 