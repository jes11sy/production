"""
Интерактивная документация API с примерами
"""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any
import json


def get_custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Создает кастомную OpenAPI схему с расширенными примерами и описаниями
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Система управления заявками - API",
        version="1.0.0",
        description="""
# 🚀 Система управления заявками

Комплексная система для управления заявками, транзакциями и пользователями с интеграцией телефонии.

## 🔐 Аутентификация

API использует JWT токены для аутентификации. Токены передаются через httpOnly cookies для безопасности.

### Процесс аутентификации:
1. Отправьте POST запрос на `/api/v1/auth/login` с логином и паролем
2. Получите JWT токен в httpOnly cookie
3. Используйте этот токен для авторизованных запросов

## 📋 Основные сущности

### 📞 Заявки (Requests)
Центральная сущность системы. Содержит информацию о клиентских заявках, включая:
- Контактные данные клиента
- Тип и статус заявки
- Назначенного мастера
- Финансовые показатели
- Прикрепленные файлы

### 💰 Транзакции (Transactions)
Финансовые операции с детализацией по:
- Типам транзакций
- Суммам и датам
- Причинам платежей
- Чеки и документы

### 👥 Пользователи (Users)
Три типа пользователей:
- **Мастера** - выполняют заявки
- **Сотрудники** - обрабатывают заявки (разные роли)
- **Администраторы** - управляют системой

## 🎯 Роли и разрешения

- **master** - доступ к своим заявкам и транзакциям
- **callcenter** - обработка заявок
- **manager** - управление пользователями
- **director** - полный доступ к отчетам
- **admin** - системное администрирование

## 📊 Мониторинг и оптимизация

Система включает:
- Мониторинг здоровья сервисов
- Оптимизацию базы данных
- Метрики производительности
- Логирование и аналитику

## 🔧 Технические особенности

- **FastAPI** с асинхронной обработкой
- **PostgreSQL** с оптимизированными индексами
- **JWT** аутентификация с httpOnly cookies
- **Pydantic** валидация данных
- **SQLAlchemy** ORM с миграциями
- **Мониторинг** здоровья системы
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://lead-schem.ru/api/v1", "description": "Production server"}
        ],
        tags=[
            {
                "name": "authentication",
                "description": "🔐 Аутентификация и авторизация пользователей"
            },
            {
                "name": "requests",
                "description": "📞 Управление заявками клиентов"
            },
            {
                "name": "transactions",
                "description": "💰 Финансовые транзакции"
            },
            {
                "name": "users",
                "description": "👥 Управление пользователями (мастера, сотрудники, администраторы)"
            },
            {
                "name": "files",
                "description": "📁 Загрузка и управление файлами"
            },
            {
                "name": "health",
                "description": "❤️ Мониторинг здоровья системы"
            },
            {
                "name": "database",
                "description": "🗄️ Мониторинг и оптимизация базы данных"
            },
            {
                "name": "recordings",
                "description": "🎵 Записи телефонных разговоров"
            }
        ]
    )
    
    # Добавляем компоненты безопасности
    openapi_schema["components"]["securitySchemes"] = {
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "JWT токен в httpOnly cookie"
        }
    }
    
    # Добавляем глобальную безопасность
    openapi_schema["security"] = [{"cookieAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Примеры данных для документации
API_EXAMPLES = {
    "auth_login": {
        "summary": "Вход в систему",
        "description": "Аутентификация пользователя с получением JWT токена",
        "value": {
            "login": "master001",
            "password": "secure_password123"
        }
    },
    "auth_login_employee": {
        "summary": "Вход сотрудника колл-центра",
        "description": "Аутентификация сотрудника с ролью callcenter",
        "value": {
            "login": "callcenter_user",
            "password": "employee_pass456"
        }
    },
    "auth_login_admin": {
        "summary": "Вход администратора",
        "description": "Аутентификация администратора системы",
        "value": {
            "login": "admin",
            "password": "admin_secure789"
        }
    },
    "request_create": {
        "summary": "Создание новой заявки",
        "description": "Создание заявки с полной информацией о клиенте",
        "value": {
            "city_id": 1,
            "request_type_id": 1,
            "client_phone": "+7 (999) 123-45-67",
            "client_name": "Иванов Иван Иванович",
            "address": "г. Москва, ул. Примерная, д. 123, кв. 45",
            "meeting_date": "2025-01-20T14:30:00",
            "direction_id": 1,
            "problem": "Не работает кондиционер, требуется диагностика",
            "status": "Новая",
            "advertising_campaign_id": 1,
            "ats_number": "ATS-2025-001",
            "call_center_name": "Петрова Анна",
            "call_center_notes": "Клиент очень вежливый, просит перезвонить после 15:00"
        }
    },
    "request_create_minimal": {
        "summary": "Минимальная заявка",
        "description": "Создание заявки с минимальным набором данных",
        "value": {
            "city_id": 1,
            "request_type_id": 2,
            "client_phone": "+7 (999) 987-65-43",
            "client_name": "Петров Петр"
        }
    },
    "request_update": {
        "summary": "Обновление заявки",
        "description": "Обновление статуса и результатов заявки мастером",
        "value": {
            "status": "completed",
            "master_notes": "Заменен фильтр кондиционера, проведена чистка",
            "result": 2500.00,
            "expenses": 450.00,
            "net_amount": 2050.00,
            "master_handover": 1230.00
        }
    },
    "transaction_create": {
        "summary": "Создание транзакции",
        "description": "Создание финансовой транзакции",
        "value": {
            "city_id": 1,
            "transaction_type_id": 1,
            "amount": 15000.50,
            "notes": "Закупка запчастей для ремонта кондиционеров",
            "specified_date": "2025-01-15",
            "payment_reason": "Материалы для заявки #123"
        }
    },
    "master_create": {
        "summary": "Создание мастера",
        "description": "Регистрация нового мастера в системе",
        "value": {
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
    },
    "employee_create": {
        "summary": "Создание сотрудника",
        "description": "Регистрация нового сотрудника колл-центра",
        "value": {
            "name": "Козлова Мария Петровна",
            "role_id": 2,
            "city_id": 1,
            "login": "maria_kozlova",
            "password": "employee_pass456",
            "notes": "Опыт работы в колл-центре 3 года"
        }
    },
    "file_upload": {
        "summary": "Загрузка файла",
        "description": "Загрузка документа или изображения",
        "value": "Выберите файл (JPG, PNG, PDF, DOC, DOCX до 10MB)"
    }
}

# Описания статусов ответов
RESPONSE_DESCRIPTIONS = {
    200: "Успешный запрос",
    201: "Ресурс успешно создан",
    400: "Некорректные данные запроса",
    401: "Требуется аутентификация",
    403: "Недостаточно прав доступа",
    404: "Ресурс не найден",
    422: "Ошибка валидации данных",
    429: "Превышен лимит запросов",
    500: "Внутренняя ошибка сервера"
}

# Примеры ответов
RESPONSE_EXAMPLES = {
    "auth_success": {
        "summary": "Успешная аутентификация",
        "value": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user_type": "master",
            "role": "master",
            "user_id": 1,
            "city_id": 1
        }
    },
    "auth_error": {
        "summary": "Ошибка аутентификации",
        "value": {
            "detail": "Incorrect login or password"
        }
    },
    "request_response": {
        "summary": "Информация о заявке",
        "value": {
            "id": 1,
            "city_id": 1,
            "request_type_id": 1,
            "client_phone": "+7 (999) 123-45-67",
            "client_name": "Иванов Иван Иванович",
            "address": "г. Москва, ул. Примерная, д. 123, кв. 45",
            "meeting_date": "2025-01-20T14:30:00",
            "status": "Новая",
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
    },
    "validation_error": {
        "summary": "Ошибка валидации",
        "value": {
            "detail": [
                {
                    "loc": ["body", "city_id"],
                    "msg": "field required",
                    "type": "value_error.missing"
                },
                {
                    "loc": ["body", "client_phone"],
                    "msg": "ensure this value has at most 20 characters",
                    "type": "value_error.any_str.max_length"
                }
            ]
        }
    },
    "health_check": {
        "summary": "Статус здоровья системы",
        "value": {
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
    }
}


def setup_api_documentation(app: FastAPI):
    """
    Настройка документации API
    """
    # Устанавливаем кастомную схему OpenAPI
    app.openapi = lambda: get_custom_openapi_schema(app)
    
    # Добавляем примеры в схемы
    _add_examples_to_schemas(app)


def _add_examples_to_schemas(app: FastAPI):
    """
    Добавляет примеры к схемам Pydantic
    """
    # Эта функция будет вызвана после создания схемы
    # Примеры будут добавлены через декораторы эндпоинтов
    pass


# Декораторы для добавления примеров к эндпоинтам
def add_examples(**examples):
    """
    Декоратор для добавления примеров к эндпоинту
    """
    def decorator(func):
        if not hasattr(func, "__annotations__"):
            func.__annotations__ = {}
        func.__examples__ = examples
        return func
    return decorator


# Утилиты для создания документации
def create_endpoint_docs(
    summary: str,
    description: str,
    examples: dict = None,
    responses: dict = None
):
    """
    Создает документацию для эндпоинта
    """
    docs = {
        "summary": summary,
        "description": description
    }
    
    if examples:
        docs["examples"] = examples
    
    if responses:
        docs["responses"] = responses
    
    return docs


# Константы для документации
COMMON_RESPONSES = {
    401: {
        "description": "Требуется аутентификация",
        "content": {
            "application/json": {
                "example": {"detail": "Not authenticated"}
            }
        }
    },
    403: {
        "description": "Недостаточно прав доступа",
        "content": {
            "application/json": {
                "example": {"detail": "Not enough permissions"}
            }
        }
    },
    422: {
        "description": "Ошибка валидации данных",
        "content": {
            "application/json": {
                "example": RESPONSE_EXAMPLES["validation_error"]["value"]
            }
        }
    },
    429: {
        "description": "Превышен лимит запросов",
        "content": {
            "application/json": {
                "example": {"detail": "Rate limit exceeded"}
            }
        }
    },
    500: {
        "description": "Внутренняя ошибка сервера",
        "content": {
            "application/json": {
                "example": {"detail": "Internal server error"}
            }
        }
    }
} 