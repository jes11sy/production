"""
Валидаторы для входных данных
"""
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException, status
from pydantic import BaseModel, validator
from .logging_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Кастомная ошибка валидации"""
    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_phone_number(phone: str) -> str:
    """Валидация номера телефона"""
    if not phone:
        raise ValidationError("Phone number is required", "phone")
    
    # Убираем все символы кроме цифр
    clean_phone = re.sub(r'\D', '', phone)
    
    # Проверяем длину
    if len(clean_phone) < 10 or len(clean_phone) > 12:
        raise ValidationError("Phone number must be between 10 and 12 digits", "phone")
    
    # Проверяем российский формат
    if len(clean_phone) == 11 and clean_phone.startswith('7'):
        return clean_phone
    elif len(clean_phone) == 10:
        return '7' + clean_phone
    elif len(clean_phone) == 11 and clean_phone.startswith('8'):
        return '7' + clean_phone[1:]
    else:
        raise ValidationError("Invalid phone number format", "phone")


def validate_email(email: str) -> str:
    """Валидация email адреса"""
    if not email:
        raise ValidationError("Email is required", "email")
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format", "email")
    
    return email.lower()


def validate_decimal_amount(amount: Any) -> Decimal:
    """Валидация денежной суммы"""
    if amount is None:
        return Decimal('0.00')
    
    try:
        decimal_amount = Decimal(str(amount))
    except (ValueError, TypeError, InvalidOperation) as e:
        raise ValidationError(f"Invalid amount format: {e}", "amount")
    
    if decimal_amount < 0:
        raise ValidationError("Amount cannot be negative", "amount")
    
    if decimal_amount > Decimal('999999.99'):
        raise ValidationError("Amount is too large", "amount")
    
    # Округляем до 2 знаков после запятой
    return decimal_amount.quantize(Decimal('0.01'))


def validate_date_range(date_from: Optional[str], date_to: Optional[str]) -> tuple[date, date]:
    """Валидация диапазона дат"""
    if not date_from or not date_to:
        raise ValidationError("Both date_from and date_to are required", "date_range")
    
    try:
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD", "date_range")
    
    if start_date > end_date:
        raise ValidationError("Start date cannot be after end date", "date_range")
    
    # Проверяем, что диапазон не слишком большой (например, не более года)
    if (end_date - start_date).days > 365:
        raise ValidationError("Date range cannot exceed 365 days", "date_range")
    
    return start_date, end_date


def validate_text_length(text: str, field_name: str, min_length: int = 0, max_length: int = 1000) -> str:
    """Валидация длины текста"""
    if not text and min_length > 0:
        raise ValidationError(f"{field_name} is required", field_name)
    
    if text and len(text) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters", field_name)
    
    if text and len(text) > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters", field_name)
    
    return text.strip() if text else ""


def validate_positive_integer(value: Any, field_name: str) -> int:
    """Валидация положительного целого числа"""
    if value is None:
        raise ValidationError(f"{field_name} is required", field_name)
    
    try:
        int_value = int(value)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"{field_name} must be a valid integer: {e}", field_name)
    
    if int_value <= 0:
        raise ValidationError(f"{field_name} must be positive", field_name)
    
    return int_value


def validate_status(status_value: str, allowed_statuses: List[str]) -> str:
    """Валидация статуса"""
    if not status_value:
        raise ValidationError("Status is required", "status")
    
    if status_value not in allowed_statuses:
        raise ValidationError(f"Invalid status. Allowed values: {', '.join(allowed_statuses)}", "status")
    
    return status_value


def sanitize_html(text: str) -> str:
    """Очистка HTML тегов из текста"""
    if not text:
        return ""
    
    # Простая очистка HTML тегов
    html_pattern = re.compile(r'<[^>]+>')
    clean_text = html_pattern.sub('', text)
    
    # Удаляем потенциально опасные символы
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        clean_text = clean_text.replace(char, '')
    
    return clean_text.strip()


class RequestValidator:
    """Валидатор для заявок"""
    
    ALLOWED_STATUSES = [
        'Ожидает', 'Ожидает Принятия', 'Принял', 'В пути', 'В работе', 'Модерн', 'Готово', 'Отказ', 'Новая', 'Перезвонить', 'ТНО'
    ]
    
    @staticmethod
    def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных заявки"""
        validated_data = {}
        
        # Валидация обязательных полей
        if 'client_phone' in data:
            validated_data['client_phone'] = validate_phone_number(data['client_phone'])
        
        if 'client_name' in data:
            validated_data['client_name'] = validate_text_length(
                data['client_name'], 'client_name', min_length=2, max_length=200
            )
        
        if 'address' in data:
            validated_data['address'] = sanitize_html(
                validate_text_length(data['address'], 'address', max_length=500)
            )
        
        if 'problem' in data:
            validated_data['problem'] = sanitize_html(
                validate_text_length(data['problem'], 'problem', max_length=1000)
            )
        
        if 'status' in data:
            validated_data['status'] = validate_status(data['status'], RequestValidator.ALLOWED_STATUSES)
        
        # Валидация денежных сумм
        for field in ['expenses', 'net_amount', 'master_handover', 'result']:
            if field in data:
                validated_data[field] = validate_decimal_amount(data[field])
        
        # Валидация ID полей
        for field in ['city_id', 'request_type_id', 'direction_id', 'master_id', 'advertising_campaign_id']:
            if field in data and data[field] is not None:
                validated_data[field] = validate_positive_integer(data[field], field)
        
        return validated_data


class TransactionValidator:
    """Валидатор для транзакций"""
    
    ALLOWED_TYPES = ['income', 'expense', 'collection']
    
    @staticmethod
    def validate_transaction_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных транзакции"""
        validated_data = {}
        
        # Валидация суммы
        if 'amount' in data:
            validated_data['amount'] = validate_decimal_amount(data['amount'])
            if validated_data['amount'] == Decimal('0.00'):
                raise ValidationError("Transaction amount cannot be zero", "amount")
        
        # Валидация заметок
        if 'notes' in data:
            validated_data['notes'] = sanitize_html(
                validate_text_length(data['notes'], 'notes', max_length=1000)
            )
        
        # Валидация даты
        if 'specified_date' in data:
            try:
                if isinstance(data['specified_date'], str):
                    validated_data['specified_date'] = datetime.strptime(
                        data['specified_date'], "%Y-%m-%d"
                    ).date()
                else:
                    validated_data['specified_date'] = data['specified_date']
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD", "specified_date")
        
        # Валидация ID полей
        for field in ['city_id', 'transaction_type_id']:
            if field in data and data[field] is not None:
                validated_data[field] = validate_positive_integer(data[field], field)
        
        return validated_data


class UserValidator:
    """Валидатор для пользователей"""
    
    @staticmethod
    def validate_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных пользователя"""
        validated_data = {}
        
        # Валидация логина
        if 'login' in data:
            login = validate_text_length(data['login'], 'login', min_length=3, max_length=50)
            if not re.match(r'^[a-zA-Z0-9_.-]+$', login):
                raise ValidationError("Login can only contain letters, numbers, dots, dashes and underscores", "login")
            validated_data['login'] = login
        
        # Валидация имени
        if 'full_name' in data:
            validated_data['full_name'] = validate_text_length(
                data['full_name'], 'full_name', min_length=2, max_length=200
            )
        
        if 'name' in data:
            validated_data['name'] = validate_text_length(
                data['name'], 'name', min_length=2, max_length=200
            )
        
        # Валидация телефона
        if 'phone_number' in data:
            validated_data['phone_number'] = validate_phone_number(data['phone_number'])
        
        # Валидация ID полей
        for field in ['city_id', 'role_id']:
            if field in data and data[field] is not None:
                validated_data[field] = validate_positive_integer(data[field], field)
        
        return validated_data


def handle_validation_error(func):
    """Декоратор для обработки ошибок валидации"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "validation_error",
                    "message": e.message,
                    "field": e.field
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper 