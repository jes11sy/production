from datetime import datetime, timedelta
from typing import Optional, Union, cast
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .database import get_db
from .models import Master, Employee, Administrator
from .schemas import TokenData
from .config import settings
from .security import LoginAttemptTracker, get_client_ip, CSRFProtection
import secrets

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка JWT
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена с улучшенной безопасностью"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Добавляем дополнительные claims для безопасности
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16),  # JWT ID для отзыва токенов
        "iss": "request_management_system"  # Issuer
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Проверка JWT токена"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def authenticate_user(login: str, password: str, db: AsyncSession) -> Optional[Union[Master, Employee, Administrator]]:
    """Аутентификация пользователя"""
    # Проверяем в таблице мастеров
    result = await db.execute(
        select(Master)
        .options(selectinload(Master.city))
        .where(Master.login == login)
    )
    user = result.scalar_one_or_none()
    
    if user and verify_password(password, str(user.password_hash)):
        return user
    
    # Проверяем в таблице сотрудников
    result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.role), selectinload(Employee.city))
        .where(Employee.login == login)
    )
    user = result.scalar_one_or_none()
    
    if user and verify_password(password, str(user.password_hash)):
        return user
    
    # Проверяем в таблице администраторов
    result = await db.execute(
        select(Administrator)
        .options(selectinload(Administrator.role))
        .where(Administrator.login == login)
    )
    user = result.scalar_one_or_none()
    
    if user and verify_password(password, str(user.password_hash)):
        return user
    
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Union[Master, Employee, Administrator]:
    """Получение текущего пользователя из httpOnly cookie с улучшенной валидацией"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Получаем токен из httpOnly cookie
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Проверяем обязательные claims
        login: str = cast(str, payload.get("sub"))
        user_type: str = cast(str, payload.get("user_type"))
        user_id: int = cast(int, payload.get("user_id"))
        
        # Проверяем дополнительные claims безопасности
        iss = payload.get("iss")
        jti = payload.get("jti")
        iat = payload.get("iat")
        
        if login is None or user_type is None or user_id is None:
            raise credentials_exception
        
        # Проверяем issuer
        if iss != "request_management_system":
            raise credentials_exception
        
        # Проверяем JWT ID (можно использовать для отзыва токенов)
        if not jti:
            raise credentials_exception
        
        # Проверяем время выдачи токена
        if not iat or datetime.utcfromtimestamp(iat) > datetime.utcnow():
            raise credentials_exception
        
        token_data = TokenData(login=login, role=user_type, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Получаем пользователя из соответствующей таблицы
    if user_type == "master":
        result = await db.execute(
            select(Master)
            .options(selectinload(Master.city))
            .where(Master.id == user_id)
        )
        user = result.scalar_one_or_none()
    elif user_type in ["director", "manager", "avitolog", "callcentr"]:
        result = await db.execute(
            select(Employee)
            .options(selectinload(Employee.role), selectinload(Employee.city))
            .where(Employee.id == user_id)
        )
        user = result.scalar_one_or_none()
    elif user_type == "admin":
        result = await db.execute(
            select(Administrator)
            .options(selectinload(Administrator.role))
            .where(Administrator.id == user_id)
        )
        user = result.scalar_one_or_none()
    else:
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Union[Master, Employee, Administrator] = Depends(get_current_user)
) -> Union[Master, Employee, Administrator]:
    """Получение активного пользователя"""
    if str(current_user.status) != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_permissions(required_roles: list):
    """Декоратор для проверки прав доступа"""
    def permission_checker(current_user: Union[Master, Employee, Administrator] = Depends(get_current_active_user)):
        if hasattr(current_user, 'role'):
            user_role = current_user.role.name
        else:
            # Для мастеров роль всегда "master"
            user_role = "master"
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    return permission_checker


# Готовые проверки прав доступа
require_admin = check_permissions(["admin"])
require_director = check_permissions(["admin", "director"])
require_manager = check_permissions(["admin", "director", "manager"])
require_avitolog = check_permissions(["admin", "director", "manager", "avitolog"])
require_callcenter = check_permissions(["admin", "director", "manager", "avitolog", "callcentr"])
require_master = check_permissions(["admin", "director", "manager", "avitolog", "master"]) 