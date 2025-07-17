"""
Расширенные схемы Pydantic с примерами для интерактивной документации
"""
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# Перечисления для статусов
class RequestStatus(str, Enum):
    NEW = "Новая"
    WAITING = "Ожидает"
    WAITING_ACCEPTANCE = "Ожидает Принятия"
    ACCEPTED = "Принял"
    ON_WAY = "В пути"
    IN_PROGRESS = "В работе"
    MODERN = "Модерн"
    COMPLETED = "Готово"
    REJECTED = "Отказ"
    CALLBACK = "Перезвонить"
    TNO = "ТНО"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserRole(str, Enum):
    MASTER = "master"
    CALLCENTER = "callcenter"
    MANAGER = "manager"
    DIRECTOR = "director"
    ADMIN = "admin"


# Базовые схемы с примерами
class CitySchema(BaseModel):
    """Схема города"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор города", example=1)
    name: str = Field(..., max_length=100, description="Название города", example="Москва")


class RequestTypeSchema(BaseModel):
    """Схема типа заявки"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор типа заявки", example=1)
    name: str = Field(..., max_length=50, description="Название типа заявки", example="Ремонт кондиционера")


class DirectionSchema(BaseModel):
    """Схема направления"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор направления", example=1)
    name: str = Field(..., max_length=50, description="Название направления", example="Бытовая техника")


class RoleSchema(BaseModel):
    """Схема роли пользователя"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор роли", example=1)
    name: str = Field(..., max_length=50, description="Название роли", example="callcenter")


class TransactionTypeSchema(BaseModel):
    """Схема типа транзакции"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор типа транзакции", example=1)
    name: str = Field(..., max_length=50, description="Название типа транзакции", example="Расход")


class AdvertisingCampaignSchema(BaseModel):
    """Схема рекламной кампании"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор кампании", example=1)
    city_id: int = Field(..., description="ID города", example=1)
    name: str = Field(..., max_length=200, description="Название кампании", example="Яндекс Директ - Ремонт кондиционеров")
    phone_number: str = Field(..., max_length=20, description="Номер телефона кампании", example="+7 (999) 123-45-67")


class MasterSchema(BaseModel):
    """Схема мастера"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор мастера", example=1)
    city_id: int = Field(..., description="ID города", example=1)
    full_name: str = Field(..., max_length=200, description="Полное имя мастера", example="Сидоров Алексей Владимирович")
    phone_number: str = Field(..., max_length=20, description="Номер телефона", example="+7 (999) 555-12-34")
    birth_date: Optional[date] = Field(None, description="Дата рождения", example="1985-03-15")
    passport: Optional[str] = Field(None, max_length=20, description="Паспортные данные", example="4510 123456")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Статус мастера", example="active")
    chat_id: Optional[str] = Field(None, max_length=100, description="ID чата Telegram", example="telegram_123456789")
    login: str = Field(..., max_length=100, description="Логин для входа", example="master_sidorov")
    notes: Optional[str] = Field(None, description="Дополнительные заметки", example="Специализация: кондиционеры, стаж 8 лет")


class EmployeeSchema(BaseModel):
    """Схема сотрудника"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор сотрудника", example=1)
    name: str = Field(..., max_length=200, description="Имя сотрудника", example="Козлова Мария Петровна")
    role_id: int = Field(..., description="ID роли", example=2)
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Статус сотрудника", example="active")
    city_id: Optional[int] = Field(None, description="ID города", example=1)
    login: str = Field(..., max_length=100, description="Логин для входа", example="maria_kozlova")
    notes: Optional[str] = Field(None, description="Дополнительные заметки", example="Опыт работы в колл-центре 3 года")
    role: Optional[RoleSchema] = Field(None, description="Информация о роли")


class AdministratorSchema(BaseModel):
    """Схема администратора"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор администратора", example=1)
    name: str = Field(..., max_length=200, description="Имя администратора", example="Админов Админ Админович")
    role_id: int = Field(..., description="ID роли", example=5)
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Статус администратора", example="active")
    login: str = Field(..., max_length=100, description="Логин для входа", example="admin")
    notes: Optional[str] = Field(None, description="Дополнительные заметки", example="Системный администратор")
    role: Optional[RoleSchema] = Field(None, description="Информация о роли")


class FileSchema(BaseModel):
    """Схема файла"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор файла", example=1)
    request_id: Optional[int] = Field(None, description="ID заявки", example=1)
    transaction_id: Optional[int] = Field(None, description="ID транзакции", example=1)
    file_type: str = Field(..., max_length=50, description="Тип файла", example="bso")
    file_path: str = Field(..., max_length=500, description="Путь к файлу", example="/media/zayvka/bso/file.jpg")


# Схемы для создания
class UserLogin(BaseModel):
    """Схема для входа в систему"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "login": "master001",
                    "password": "secure_password123"
                },
                {
                    "login": "callcenter_user", 
                    "password": "employee_pass456"
                },
                {
                    "login": "admin",
                    "password": "admin_secure789"
                }
            ]
        }
    )
    
    login: str = Field(..., description="Логин пользователя", example="master001")
    password: str = Field(..., description="Пароль пользователя", example="secure_password123")


class RequestCreateSchema(BaseModel):
    """Схема для создания заявки"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
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
                },
                {
                    "city_id": 1,
                    "request_type_id": 2,
                    "client_phone": "+7 (999) 987-65-43",
                    "client_name": "Петров Петр"
                }
            ]
        }
    )
    
    advertising_campaign_id: Optional[int] = Field(None, description="ID рекламной кампании", example=1)
    city_id: int = Field(..., description="ID города (обязательно)", example=1)
    request_type_id: Optional[int] = Field(None, description="ID типа заявки", example=1)
    client_phone: str = Field(..., max_length=20, description="Телефон клиента", example="+7 (999) 123-45-67")
    client_name: Optional[str] = Field(None, max_length=200, description="Имя клиента", example="Иванов Иван Иванович")
    address: Optional[str] = Field(None, description="Адрес клиента", example="г. Москва, ул. Примерная, д. 123, кв. 45")
    meeting_date: Optional[datetime] = Field(None, description="Дата и время встречи", example="2025-01-20T14:30:00")
    direction_id: Optional[int] = Field(None, description="ID направления", example=1)
    problem: Optional[str] = Field(None, description="Описание проблемы", example="Не работает кондиционер, требуется диагностика")
    status: RequestStatus = Field(default=RequestStatus.NEW, description="Статус заявки", example="Новая")
    master_id: Optional[int] = Field(None, description="ID назначенного мастера", example=1)
    master_notes: Optional[str] = Field(None, description="Заметки мастера", example="Требуется дополнительная диагностика")
    result: Optional[Decimal] = Field(None, decimal_places=2, description="Результат работы (сумма)", example=2500.00)
    expenses: Decimal = Field(default=Decimal('0.00'), decimal_places=2, description="Расходы", example=450.00)
    net_amount: Decimal = Field(default=Decimal('0.00'), decimal_places=2, description="Чистая сумма", example=2050.00)
    master_handover: Decimal = Field(default=Decimal('0.00'), decimal_places=2, description="Передача мастеру", example=1230.00)
    ats_number: Optional[str] = Field(None, max_length=50, description="Номер АТС", example="ATS-2025-001")
    call_center_name: Optional[str] = Field(None, max_length=200, description="Имя сотрудника колл-центра", example="Петрова Анна")
    call_center_notes: Optional[str] = Field(None, description="Заметки колл-центра", example="Клиент очень вежливый, просит перезвонить после 15:00")
    avito_chat_id: Optional[str] = Field(None, max_length=100, description="ID чата Avito", example="avito_chat_123")
    
    @validator('meeting_date', pre=True)
    @classmethod
    def validate_meeting_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class RequestUpdateSchema(BaseModel):
    """Схема для обновления заявки"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "completed",
                    "master_notes": "Заменен фильтр кондиционера, проведена чистка",
                    "result": 2500.00,
                    "expenses": 450.00,
                    "net_amount": 2050.00,
                    "master_handover": 1230.00
                },
                {
                    "status": "in_progress",
                    "master_id": 1,
                    "master_notes": "Начата диагностика"
                }
            ]
        }
    )
    
    advertising_campaign_id: Optional[int] = Field(None, description="ID рекламной кампании")
    city_id: Optional[int] = Field(None, description="ID города")
    request_type_id: Optional[int] = Field(None, description="ID типа заявки")
    client_phone: Optional[str] = Field(None, max_length=20, description="Телефон клиента")
    client_name: Optional[str] = Field(None, max_length=200, description="Имя клиента")
    address: Optional[str] = Field(None, description="Адрес клиента")
    meeting_date: Optional[datetime] = Field(None, description="Дата и время встречи")
    direction_id: Optional[int] = Field(None, description="ID направления")
    problem: Optional[str] = Field(None, description="Описание проблемы")
    status: Optional[RequestStatus] = Field(None, description="Статус заявки", example="completed")
    master_id: Optional[int] = Field(None, description="ID назначенного мастера")
    master_notes: Optional[str] = Field(None, description="Заметки мастера", example="Заменен фильтр кондиционера, проведена чистка")
    result: Optional[Decimal] = Field(None, decimal_places=2, description="Результат работы (сумма)", example=2500.00)
    expenses: Optional[Decimal] = Field(None, decimal_places=2, description="Расходы", example=450.00)
    net_amount: Optional[Decimal] = Field(None, decimal_places=2, description="Чистая сумма", example=2050.00)
    master_handover: Optional[Decimal] = Field(None, decimal_places=2, description="Передача мастеру", example=1230.00)
    ats_number: Optional[str] = Field(None, max_length=50, description="Номер АТС")
    call_center_name: Optional[str] = Field(None, max_length=200, description="Имя сотрудника колл-центра")
    call_center_notes: Optional[str] = Field(None, description="Заметки колл-центра")
    avito_chat_id: Optional[str] = Field(None, max_length=100, description="ID чата Avito")


class RequestResponseSchema(BaseModel):
    """Схема ответа с информацией о заявке"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор заявки", example=1)
    city_id: int = Field(..., description="ID города", example=1)
    request_type_id: Optional[int] = Field(None, description="ID типа заявки", example=1)
    client_phone: str = Field(..., description="Телефон клиента", example="+7 (999) 123-45-67")
    client_name: Optional[str] = Field(None, description="Имя клиента", example="Иванов Иван Иванович")
    address: Optional[str] = Field(None, description="Адрес клиента", example="г. Москва, ул. Примерная, д. 123, кв. 45")
    meeting_date: Optional[datetime] = Field(None, description="Дата и время встречи", example="2025-01-20T14:30:00")
    status: str = Field(..., description="Статус заявки", example="new")
    created_at: datetime = Field(..., description="Дата создания", example="2025-01-15T10:30:00")
    
    # Связанные объекты
    advertising_campaign: Optional[AdvertisingCampaignSchema] = Field(None, description="Рекламная кампания")
    city: CitySchema = Field(..., description="Город")
    request_type: Optional[RequestTypeSchema] = Field(None, description="Тип заявки")
    direction: Optional[DirectionSchema] = Field(None, description="Направление")
    master: Optional[MasterSchema] = Field(None, description="Назначенный мастер")
    files: List[FileSchema] = Field(default=[], description="Прикрепленные файлы")
    
    # Пути к файлам
    bso_file_path: Optional[str] = Field(None, description="Путь к файлу БСО")
    expense_file_path: Optional[str] = Field(None, description="Путь к файлу расходов")
    recording_file_path: Optional[str] = Field(None, description="Путь к записи разговора")


class TransactionCreateSchema(BaseModel):
    """Схема для создания транзакции"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "city_id": 1,
                    "transaction_type_id": 1,
                    "amount": 15000.50,
                    "notes": "Закупка запчастей для ремонта кондиционеров",
                    "specified_date": "2025-01-15",
                    "payment_reason": "Материалы для заявки #123"
                },
                {
                    "city_id": 1,
                    "transaction_type_id": 2,
                    "amount": 5000.00,
                    "notes": "Оплата услуг мастера",
                    "specified_date": "2025-01-15",
                    "payment_reason": "Заработная плата"
                }
            ]
        }
    )
    
    city_id: int = Field(..., description="ID города", example=1)
    transaction_type_id: int = Field(..., description="ID типа транзакции", example=1)
    amount: Decimal = Field(..., decimal_places=2, description="Сумма транзакции", example=15000.50)
    notes: Optional[str] = Field(None, description="Примечания", example="Закупка запчастей для ремонта кондиционеров")
    specified_date: date = Field(..., description="Дата операции", example="2025-01-15")
    payment_reason: Optional[str] = Field(None, description="Причина платежа", example="Материалы для заявки #123")
    expense_receipt_path: Optional[str] = Field(None, description="Путь к чеку", example="/media/receipts/receipt_123.jpg")


class TransactionResponseSchema(BaseModel):
    """Схема ответа с информацией о транзакции"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Уникальный идентификатор транзакции", example=1)
    city_id: int = Field(..., description="ID города", example=1)
    transaction_type_id: int = Field(..., description="ID типа транзакции", example=1)
    amount: Decimal = Field(..., description="Сумма транзакции", example=15000.50)
    notes: Optional[str] = Field(None, description="Примечания", example="Закупка запчастей")
    specified_date: date = Field(..., description="Дата операции", example="2025-01-15")
    payment_reason: Optional[str] = Field(None, description="Причина платежа", example="Материалы для заявки #123")
    expense_receipt_path: Optional[str] = Field(None, description="Путь к чеку")
    created_at: datetime = Field(..., description="Дата создания", example="2025-01-15T10:30:00")
    
    # Связанные объекты
    city: CitySchema = Field(..., description="Город")
    transaction_type: TransactionTypeSchema = Field(..., description="Тип транзакции")


class MasterCreateSchema(BaseModel):
    """Схема для создания мастера"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
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
            ]
        }
    )
    
    city_id: int = Field(..., description="ID города", example=1)
    full_name: str = Field(..., max_length=200, description="Полное имя", example="Сидоров Алексей Владимирович")
    phone_number: str = Field(..., max_length=20, description="Номер телефона", example="+7 (999) 555-12-34")
    birth_date: Optional[date] = Field(None, description="Дата рождения", example="1985-03-15")
    passport: Optional[str] = Field(None, max_length=20, description="Паспортные данные", example="4510 123456")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Статус", example="active")
    chat_id: Optional[str] = Field(None, max_length=100, description="ID чата Telegram", example="telegram_123456789")
    login: str = Field(..., max_length=100, description="Логин", example="master_sidorov")
    password: str = Field(..., min_length=6, description="Пароль", example="secure_pass123")
    notes: Optional[str] = Field(None, description="Заметки", example="Специализация: кондиционеры, стаж 8 лет")


class EmployeeCreateSchema(BaseModel):
    """Схема для создания сотрудника"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Козлова Мария Петровна",
                    "role_id": 2,
                    "city_id": 1,
                    "login": "maria_kozlova",
                    "password": "employee_pass456",
                    "notes": "Опыт работы в колл-центре 3 года"
                }
            ]
        }
    )
    
    name: str = Field(..., max_length=200, description="Имя сотрудника", example="Козлова Мария Петровна")
    role_id: int = Field(..., description="ID роли", example=2)
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Статус", example="active")
    city_id: Optional[int] = Field(None, description="ID города", example=1)
    login: str = Field(..., max_length=100, description="Логин", example="maria_kozlova")
    password: str = Field(..., min_length=6, description="Пароль", example="employee_pass456")
    notes: Optional[str] = Field(None, description="Заметки", example="Опыт работы в колл-центре 3 года")


class TokenResponse(BaseModel):
    """Схема ответа с токеном"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user_type": "master",
                    "role": "master",
                    "user_id": 1,
                    "city_id": 1
                }
            ]
        }
    )
    
    access_token: str = Field(..., description="JWT токен доступа", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(..., description="Тип токена", example="bearer")
    user_type: str = Field(..., description="Тип пользователя", example="master")
    role: str = Field(..., description="Роль пользователя", example="master")
    user_id: int = Field(..., description="ID пользователя", example=1)
    city_id: Optional[int] = Field(None, description="ID города пользователя", example=1)


class ErrorResponse(BaseModel):
    """Схема ответа с ошибкой"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "Incorrect login or password"
                },
                {
                    "detail": "Not authenticated"
                },
                {
                    "detail": "Not enough permissions"
                }
            ]
        }
    )
    
    detail: str = Field(..., description="Описание ошибки", example="Incorrect login or password")


class ValidationErrorResponse(BaseModel):
    """Схема ответа с ошибкой валидации"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
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
            ]
        }
    )
    
    detail: List[dict] = Field(..., description="Детали ошибок валидации")


class HealthCheckResponse(BaseModel):
    """Схема ответа проверки здоровья"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
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
                        }
                    }
                }
            ]
        }
    )
    
    status: str = Field(..., description="Общий статус системы", example="healthy")
    timestamp: str = Field(..., description="Время проверки", example="2025-01-15T15:00:00Z")
    service: str = Field(..., description="Название сервиса", example="Request Management System")
    version: str = Field(..., description="Версия системы", example="1.0.0")
    checks: Optional[dict] = Field(None, description="Детальные проверки компонентов") 