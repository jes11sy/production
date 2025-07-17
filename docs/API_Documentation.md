# 📚 API Documentation

## 🔗 Базовые настройки

**Base URL:** `http://localhost:8000/api/v1`  
**Аутентификация:** httpOnly cookies  
**Content-Type:** `application/json`  

## 👥 Роли пользователей

Система поддерживает следующие роли с различными уровнями доступа:

- **admin** - Полный доступ ко всем функциям
- **director** - Доступ к заявкам, мастерам, транзакциям
- **manager** - Доступ к управлению заявками и пользователями
- **avitolog** - Доступ к работе с заявками
- **callcentr** - Ограниченный доступ: заявки, входящие заявки, отчет КЦ
- **master** - Доступ к своим заявкам и транзакциям

## 🔐 Аутентификация

### POST /auth/login
Вход в систему

**Request:**
```json
{
  "login": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "login": "admin",
    "status": "active",
    "user_type": "admin"
  }
}
```

### GET /auth/me
Получение информации о текущем пользователе

**Headers:** `Cookie: access_token=...`

**Response:**
```json
{
  "id": 1,
  "login": "admin",
  "status": "active",
  "user_type": "admin"
}
```

### POST /auth/logout
Выход из системы

**Headers:** `Cookie: access_token=...`

**Response:** `200 OK`

---

## 👥 Пользователи

### GET /users/masters
Получение списка мастеров

**Response:**
```json
[
  {
    "id": 1,
    "city_id": 1,
    "full_name": "Иван Иванов",
    "phone_number": "+7 (900) 123-45-67",
    "birth_date": "1990-01-01",
    "passport": "1234 567890",
    "status": "active",
    "chat_id": "123456789",
    "login": "master1",
    "notes": "Заметки",
    "created_at": "2023-01-01T12:00:00Z",
    "city": {
      "id": 1,
      "name": "Москва",
      "created_at": "2023-01-01T12:00:00Z"
    }
  }
]
```

### POST /users/masters
Создание нового мастера

**Request:**
```json
{
  "city_id": 1,
  "full_name": "Иван Иванов",
  "phone_number": "+7 (900) 123-45-67",
  "birth_date": "1990-01-01",
  "passport": "1234 567890",
  "login": "master1",
  "password": "password123",
  "notes": "Заметки"
}
```

### GET /users/employees
Получение списка сотрудников

**Response:**
```json
[
  {
    "id": 1,
    "name": "Сергей Петров",
    "role_id": 2,
    "status": "active",
    "city_id": 1,
    "login": "employee1",
    "notes": "Заметки",
    "created_at": "2023-01-01T12:00:00Z",
    "role": {
      "id": 2,
      "name": "manager"
    },
    "city": {
      "id": 1,
      "name": "Москва",
      "created_at": "2023-01-01T12:00:00Z"
    }
  }
]
```

### GET /users/administrators
Получение списка администраторов

**Response:**
```json
[
  {
    "id": 1,
    "name": "Алексей Сидоров",
    "role_id": 1,
    "status": "active",
    "login": "admin1",
    "notes": "Заметки",
    "created_at": "2023-01-01T12:00:00Z",
    "role": {
      "id": 1,
      "name": "admin"
    }
  }
]
```

---

## 📝 Заявки

### GET /requests/
Получение списка заявок

**Query Parameters:**
- `status` (optional): Фильтр по статусу
- `city_id` (optional): Фильтр по городу
- `master_id` (optional): Фильтр по мастеру

**Response:**
```json
[
  {
    "id": 1,
    "advertising_campaign_id": 1,
    "city_id": 1,
    "request_type_id": 1,
    "client_phone": "+7 (900) 123-45-67",
    "client_name": "Мария Смирнова",
    "address": "ул. Ленина, 10",
    "meeting_date": "2023-01-15T14:00:00Z",
    "direction_id": 1,
    "problem": "Не работает кран",
    "status": "new",
    "master_id": null,
    "master_notes": null,
    "result": null,
    "expenses": 0,
    "net_amount": 0,
    "master_handover": 0,
    "ats_number": "12345",
    "call_center_name": "Центр обслуживания",
    "call_center_notes": "Заметки",
    "avito_chat_id": "chat123",
    "created_at": "2023-01-01T12:00:00Z",
    "advertising_campaign": {
      "id": 1,
      "city_id": 1,
      "name": "Авито реклама",
      "phone_number": "+7 (900) 000-00-00",
      "city": {
        "id": 1,
        "name": "Москва",
        "created_at": "2023-01-01T12:00:00Z"
      }
    },
    "city": {
      "id": 1,
      "name": "Москва",
      "created_at": "2023-01-01T12:00:00Z"
    },
    "request_type": {
      "id": 1,
      "name": "Сантехника"
    },
    "direction": {
      "id": 1,
      "name": "Ремонт"
    },
    "master": null,
    "files": []
  }
]
```

### POST /requests/
Создание новой заявки

**Request:**
```json
{
  "advertising_campaign_id": 1,
  "city_id": 1,
  "request_type_id": 1,
  "client_phone": "+7 (900) 123-45-67",
  "client_name": "Мария Смирнова",
  "address": "ул. Ленина, 10",
  "meeting_date": "2023-01-15T14:00:00Z",
  "direction_id": 1,
  "problem": "Не работает кран",
  "status": "new",
  "ats_number": "12345",
  "call_center_name": "Центр обслуживания",
  "call_center_notes": "Заметки",
  "avito_chat_id": "chat123"
}
```

### GET /requests/{id}
Получение заявки по ID

**Response:** Аналогично GET /requests/, но один объект

### PUT /requests/{id}
Обновление заявки

**Request:** Аналогично POST /requests/

### DELETE /requests/{id}
Удаление заявки

**Response:** `200 OK`

### GET /requests/callcenter-report
Получение отчета для колл-центра

**Требуемые права:** callcentr, avitolog, manager, director, admin

**Query Parameters:**
- `city_id` (optional): Фильтр по городу
- `status` (optional): Фильтр по статусу
- `date_from` (optional): Дата начала периода (YYYY-MM-DD)
- `date_to` (optional): Дата окончания периода (YYYY-MM-DD)

**Response:**
```json
{
  "statistics": {
    "total": 150,
    "new": 45,
    "in_progress": 30,
    "done": 65,
    "cancelled": 10
  },
  "requests": [
    {
      "id": 1,
      "client_phone": "+7 (900) 123-45-67",
      "client_name": "Мария Смирнова",
      "address": "ул. Ленина, 10",
      "status": "new",
      "city_name": "Москва",
      "created_at": "2023-01-01T12:00:00Z",
      "advertising_campaign_name": "Авито реклама",
      "request_type_name": "Впервые"
    }
  ]
}
```

---

## 💰 Транзакции

### GET /transactions/
Получение списка транзакций

**Query Parameters:**
- `city_id` (optional): Фильтр по городу
- `transaction_type_id` (optional): Фильтр по типу транзакции

**Response:**
```json
[
  {
    "id": 1,
    "city_id": 1,
    "transaction_type_id": 1,
    "amount": 5000.00,
    "notes": "Оплата за услуги",
    "specified_date": "2023-01-01",
    "created_at": "2023-01-01T12:00:00Z",
    "city": {
      "id": 1,
      "name": "Москва",
      "created_at": "2023-01-01T12:00:00Z"
    },
    "transaction_type": {
      "id": 1,
      "name": "Приход"
    },
    "files": []
  }
]
```

### POST /transactions/
Создание новой транзакции

**Request:**
```json
{
  "city_id": 1,
  "transaction_type_id": 1,
  "amount": 5000.00,
  "notes": "Оплата за услуги",
  "specified_date": "2023-01-01"
}
```

### GET /transactions/{id}
Получение транзакции по ID

### PUT /transactions/{id}
Обновление транзакции

### DELETE /transactions/{id}
Удаление транзакции

---

## 📊 Справочники

### GET /cities/
Получение списка городов

**Response:**
```json
[
  {
    "id": 1,
    "name": "Москва",
    "created_at": "2023-01-01T12:00:00Z"
  }
]
```

### GET /roles/
Получение списка ролей

**Response:**
```json
[
  {
    "id": 1,
    "name": "admin"
  }
]
```

### GET /request-types/
Получение типов заявок

**Response:**
```json
[
  {
    "id": 1,
    "name": "Сантехника"
  }
]
```

### GET /directions/
Получение направлений

**Response:**
```json
[
  {
    "id": 1,
    "name": "Ремонт"
  }
]
```

### GET /transaction-types/
Получение типов транзакций

**Response:**
```json
[
  {
    "id": 1,
    "name": "Приход"
  }
]
```

### GET /advertising-campaigns/
Получение рекламных кампаний

**Response:**
```json
[
  {
    "id": 1,
    "city_id": 1,
    "name": "Авито реклама",
    "phone_number": "+7 (900) 000-00-00",
    "city": {
      "id": 1,
      "name": "Москва",
      "created_at": "2023-01-01T12:00:00Z"
    }
  }
]
```

---

## 📎 Файлы

### POST /upload-expense-receipt/
Загрузка чека расходов

**Request:** `multipart/form-data`
- `file`: Файл изображения

**Response:**
```json
{
  "filename": "expense_receipt_123.jpg",
  "path": "media/expenses/expense_receipt_123.jpg"
}
```

### POST /upload-bso/
Загрузка БСО

**Request:** `multipart/form-data`
- `file`: Файл изображения

**Response:**
```json
{
  "filename": "bso_123.jpg",
  "path": "media/bso/bso_123.jpg"
}
```

### POST /upload-recording/
Загрузка записи

**Request:** `multipart/form-data`
- `file`: Аудио файл

**Response:**
```json
{
  "filename": "recording_123.mp3",
  "path": "media/recordings/recording_123.mp3"
}
```

---

## 🔧 Статусы и коды ошибок

### HTTP Status Codes
- `200 OK` - Успешный запрос
- `201 Created` - Ресурс создан
- `400 Bad Request` - Неверные параметры
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Ресурс не найден
- `422 Unprocessable Entity` - Ошибка валидации
- `500 Internal Server Error` - Внутренняя ошибка сервера

### Статусы заявок
- `new` - Новая заявка
- `assigned` - Назначена мастеру
- `in_progress` - В работе
- `done` - Выполнена
- `cancelled` - Отменена

### Статусы пользователей
- `active` - Активен
- `inactive` - Неактивен
- `pending` - Ожидает подтверждения

---

## 🛠️ Примеры использования

### Создание и обработка заявки
```javascript
// 1. Создание новой заявки
const newRequest = await fetch('/api/v1/requests/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    city_id: 1,
    request_type_id: 1,
    client_phone: '+7 (900) 123-45-67',
    client_name: 'Мария Смирнова',
    problem: 'Не работает кран',
    status: 'new'
  })
});

// 2. Назначение мастера
const updatedRequest = await fetch(`/api/v1/requests/${requestId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    master_id: 5,
    status: 'assigned'
  })
});

// 3. Завершение заявки
const completedRequest = await fetch(`/api/v1/requests/${requestId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    status: 'done',
    result: 'Кран отремонтирован',
    net_amount: 2000,
    expenses: 500,
    master_handover: 1500
  })
});
```

---

## 🎧 Система записей звонков

### POST /recordings/download
Запуск ручной загрузки записей

**Требуемые права:** admin

**Response:**
```json
{
  "message": "Download started",
  "status": "success"
}
```

### GET /recordings/status
Получение статуса сервиса записей

**Response:**
```json
{
  "status": "running",
  "last_check": "2023-01-01T12:00:00Z",
  "processed_files": 25
}
```

### POST /recordings/start
Запуск сервиса записей

**Требуемые права:** admin

### POST /recordings/stop
Остановка сервиса записей

**Требуемые права:** admin

**Описание:**
Система автоматически загружает записи звонков из email (Rambler) и связывает их с заявками по номеру телефона и времени звонка. Записи сохраняются в `media/zayvka/zapis/` с именем формата: `YYYY.MM.DD__HH-MM-SS__from_number__to_number.ext`

---

## 🔧 Webhook интеграции

### POST /mango/webhook
Webhook для интеграции с Mango Office

**Описание:**
Автоматически создает заявки при входящих звонках. Определяет тип заявки ("Впервые" или "Повтор") на основе истории звонков клиента.

**Защита от дублирования:**
- Проверка существующих заявок за последние 30 минут
- Двойная проверка перед созданием
- Обработка ошибок с откатом транзакций
```

### Работа с транзакциями
```javascript
// Получение баланса по городам
const transactions = await fetch('/api/v1/transactions/', {
  credentials: 'include'
});

// Создание транзакции прихода
const income = await fetch('/api/v1/transactions/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    city_id: 1,
    transaction_type_id: 1, // Приход
    amount: 10000,
    notes: 'Оплата за услуги',
    specified_date: '2023-01-01'
  })
});

// Создание транзакции расхода
const expense = await fetch('/api/v1/transactions/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    city_id: 1,
    transaction_type_id: 2, // Расход
    amount: -3000,
    notes: 'Закупка материалов',
    specified_date: '2023-01-01'
  })
});
``` 