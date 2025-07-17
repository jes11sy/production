"""
Утилиты для оптимизации производительности
"""
import time
import functools
from typing import Callable, Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from ..core.models import Request, Transaction, Master, Employee, Administrator
from ..logging_config import log_performance


def performance_monitor(func: Callable) -> Callable:
    """Декоратор для мониторинга производительности функций"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            log_performance(func.__name__, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            log_performance(func.__name__, execution_time, {"error": str(e)})
            raise
    return wrapper


async def get_requests_optimized(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    include_relations: bool = True
) -> List[Request]:
    """
    Оптимизированная загрузка заявок с минимальным количеством запросов
    """
    query = select(Request)
    
    if include_relations:
        # Используем joinedload для связей many-to-one и selectinload для one-to-many
        query = query.options(
            joinedload(Request.advertising_campaign),
            joinedload(Request.city),
            joinedload(Request.request_type),
            joinedload(Request.direction),
            joinedload(Request.master).joinedload(Master.city),
            selectinload(Request.files)
        )
    
    query = query.offset(skip).limit(limit).order_by(Request.created_at.desc())
    
    result = await db.execute(query)
    return list(result.unique().scalars().all())


async def get_request_optimized(
    db: AsyncSession, 
    request_id: int,
    include_relations: bool = True
) -> Request | None:
    """
    Оптимизированная загрузка одной заявки
    """
    query = select(Request).where(Request.id == request_id)
    
    if include_relations:
        query = query.options(
            joinedload(Request.advertising_campaign),
            joinedload(Request.city),
            joinedload(Request.request_type),
            joinedload(Request.direction),
            joinedload(Request.master).joinedload(Master.city),
            selectinload(Request.files)
        )
    
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def get_transactions_optimized(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    include_relations: bool = True
) -> List[Transaction]:
    """
    Оптимизированная загрузка транзакций
    """
    query = select(Transaction)
    
    if include_relations:
        query = query.options(
            joinedload(Transaction.city),
            joinedload(Transaction.transaction_type),
            selectinload(Transaction.files)
        )
    
    query = query.offset(skip).limit(limit).order_by(Transaction.created_at.desc())
    
    result = await db.execute(query)
    return list(result.unique().scalars().all())


async def get_masters_optimized(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    city_id: int | None = None
) -> List[Master]:
    """
    Оптимизированная загрузка мастеров
    """
    query = select(Master).options(joinedload(Master.city))
    
    if city_id:
        query = query.where(Master.city_id == city_id)
    
    query = query.offset(skip).limit(limit).order_by(Master.created_at.desc())
    
    result = await db.execute(query)
    return list(result.unique().scalars().all())


async def get_employees_optimized(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    role_id: int | None = None
) -> List[Employee]:
    """
    Оптимизированная загрузка сотрудников
    """
    query = select(Employee).options(
        joinedload(Employee.role),
        joinedload(Employee.city)
    )
    
    if role_id:
        query = query.where(Employee.role_id == role_id)
    
    query = query.offset(skip).limit(limit).order_by(Employee.created_at.desc())
    
    result = await db.execute(query)
    return list(result.unique().scalars().all())


class QueryCache:
    """Простой кеш для часто используемых запросов"""
    
    def __init__(self, ttl: int = 300):  # 5 минут
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Any | None:
        """Получить значение из кеша"""
        if key in self.cache:
            cache_entry = self.cache[key]
            if time.time() - cache_entry['timestamp'] < self.ttl:
                return cache_entry['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Сохранить значение в кеш"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        """Очистить кеш"""
        self.cache.clear()


# Глобальный экземпляр кеша
query_cache = QueryCache()


async def get_cities_cached(db: AsyncSession) -> List[Dict[str, Any]]:
    """Получить список городов с кешированием"""
    cache_key = "cities_list"
    cached_result = query_cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
    
    from ..core.models import City
    result = await db.execute(select(City).order_by(City.name))
    cities = [{"id": city.id, "name": city.name} for city in result.scalars().all()]
    
    query_cache.set(cache_key, cities)
    return cities


async def get_request_types_cached(db: AsyncSession) -> List[Dict[str, Any]]:
    """Получить типы заявок с кешированием"""
    cache_key = "request_types_list"
    cached_result = query_cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
    
    from ..core.models import RequestType
    result = await db.execute(select(RequestType).order_by(RequestType.name))
    request_types = [{"id": rt.id, "name": rt.name} for rt in result.scalars().all()]
    
    query_cache.set(cache_key, request_types)
    return request_types


async def get_directions_cached(db: AsyncSession) -> List[Dict[str, Any]]:
    """Получить направления с кешированием"""
    cache_key = "directions_list"
    cached_result = query_cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
    
    from ..core.models import Direction
    result = await db.execute(select(Direction).order_by(Direction.name))
    directions = [{"id": d.id, "name": d.name} for d in result.scalars().all()]
    
    query_cache.set(cache_key, directions)
    return directions


def invalidate_cache_on_change(cache_keys: List[str]):
    """Декоратор для инвалидации кеша при изменении данных"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Инвалидируем кеш после успешного выполнения
            for key in cache_keys:
                if key in query_cache.cache:
                    del query_cache.cache[key]
            return result
        return wrapper
    return decorator 