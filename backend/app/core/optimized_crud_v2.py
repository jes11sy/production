"""
Оптимизированные CRUD операции с кешированием для максимальной производительности
Исправляет N+1 запросы и добавляет кеширование
"""
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, desc, asc
from sqlalchemy.orm import selectinload, joinedload, contains_eager
from datetime import datetime, timedelta, date
import logging
import asyncio
from functools import wraps

from .models import (
    Request, Transaction, Master, Employee, Administrator, 
    City, RequestType, Direction, AdvertisingCampaign, TransactionType,
    File, Role
)
from .schemas import RequestCreate, RequestUpdate, TransactionCreate, TransactionUpdate
from .cache import cache_manager, QueryCache, cached
from .performance import performance_monitor

logger = logging.getLogger(__name__)

class OptimizedCRUDv2:
    """Оптимизированные CRUD операции с кешированием"""
    
    # === СПРАВОЧНИКИ (кешируются на длительное время) ===
    
    @staticmethod
    @cached(ttl=3600, key_prefix="reference")
    async def get_cities_cached(db: AsyncSession) -> List[Dict[str, Any]]:
        """Получение списка городов с кешированием"""
        result = await db.execute(select(City).order_by(City.name))
        cities = result.scalars().all()
        return [{"id": city.id, "name": city.name} for city in cities]
    
    @staticmethod
    @cached(ttl=3600, key_prefix="reference")
    async def get_request_types_cached(db: AsyncSession) -> List[Dict[str, Any]]:
        """Получение типов заявок с кешированием"""
        result = await db.execute(select(RequestType).order_by(RequestType.name))
        types = result.scalars().all()
        return [{"id": t.id, "name": t.name} for t in types]
    
    @staticmethod
    @cached(ttl=3600, key_prefix="reference")
    async def get_directions_cached(db: AsyncSession) -> List[Dict[str, Any]]:
        """Получение направлений с кешированием"""
        result = await db.execute(select(Direction).order_by(Direction.name))
        directions = result.scalars().all()
        return [{"id": d.id, "name": d.name} for d in directions]
    
    @staticmethod
    @cached(ttl=1800, key_prefix="reference")
    async def get_advertising_campaigns_cached(db: AsyncSession) -> List[Dict[str, Any]]:
        """Получение рекламных кампаний с кешированием"""
        result = await db.execute(
            select(AdvertisingCampaign)
            .options(joinedload(AdvertisingCampaign.city))
            .order_by(AdvertisingCampaign.name)
        )
        campaigns = result.unique().scalars().all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "phone_number": c.phone_number,
                "city_id": c.city_id,
                "city_name": c.city.name if c.city else None
            }
            for c in campaigns
        ]
    
    # === ПОЛЬЗОВАТЕЛИ (кешируются на короткое время) ===
    
    @staticmethod
    @cached(ttl=900, key_prefix="users")
    async def get_masters_by_city_cached(db: AsyncSession, city_id: int) -> List[Dict[str, Any]]:
        """Получение мастеров по городу с кешированием"""
        result = await db.execute(
            select(Master)
            .options(joinedload(Master.city))
            .where(and_(Master.city_id == city_id, Master.status == 'active'))
            .order_by(Master.full_name)
        )
        masters = result.unique().scalars().all()
        return [
            {
                "id": m.id,
                "full_name": m.full_name,
                "phone_number": m.phone_number,
                "city_id": m.city_id,
                "city_name": m.city.name if m.city else None,
                "status": m.status
            }
            for m in masters
        ]
    
    @staticmethod
    @cached(ttl=900, key_prefix="users")
    async def authenticate_user_cached(db: AsyncSession, login: str) -> Optional[Dict[str, Any]]:
        """Аутентификация пользователя с кешированием"""
        # Проверяем мастеров
        master_result = await db.execute(
            select(Master)
            .options(joinedload(Master.city))
            .where(Master.login == login)
        )
        user = master_result.unique().scalar_one_or_none()
        if user:
            return {
                "id": user.id,
                "login": user.login,
                "password_hash": user.password_hash,
                "status": user.status,
                "user_type": "master",
                "full_name": user.full_name,
                "city_id": user.city_id,
                "city_name": user.city.name if user.city else None
            }
        
        # Проверяем сотрудников
        employee_result = await db.execute(
            select(Employee)
            .options(joinedload(Employee.role), joinedload(Employee.city))
            .where(Employee.login == login)
        )
        user = employee_result.unique().scalar_one_or_none()
        if user:
            return {
                "id": user.id,
                "login": user.login,
                "password_hash": user.password_hash,
                "status": user.status,
                "user_type": "employee",
                "name": user.name,
                "role_id": user.role_id,
                "role_name": user.role.name if user.role else None,
                "city_id": user.city_id,
                "city_name": user.city.name if user.city else None
            }
        
        # Проверяем администраторов
        admin_result = await db.execute(
            select(Administrator)
            .options(joinedload(Administrator.role))
            .where(Administrator.login == login)
        )
        user = admin_result.unique().scalar_one_or_none()
        if user:
            return {
                "id": user.id,
                "login": user.login,
                "password_hash": user.password_hash,
                "status": user.status,
                "user_type": "admin",
                "name": user.name,
                "role_id": user.role_id,
                "role_name": user.role.name if user.role else None
            }
        
        return None
    
    # === ЗАЯВКИ (оптимизированные запросы) ===
    
    @staticmethod
    @performance_monitor
    async def get_requests_optimized(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        city_id: Optional[int] = None,
        status: Optional[str] = None,
        master_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        phone_filter: Optional[str] = None
    ) -> List[Request]:
        """
        Оптимизированное получение заявок с фильтрацией и пагинацией
        Исправляет N+1 проблемы через правильное использование joinedload/selectinload
        """
        # Базовый запрос с оптимизированной загрузкой связей
        query = select(Request).options(
            # many-to-one связи загружаем через joinedload
            joinedload(Request.city),
            joinedload(Request.request_type),
            joinedload(Request.advertising_campaign),
            joinedload(Request.direction),
            joinedload(Request.master).joinedload(Master.city),
            # one-to-many связи загружаем через selectinload
            selectinload(Request.files)
        )
        
        # Применяем фильтры с использованием индексов
        filters = []
        
        if city_id:
            filters.append(Request.city_id == city_id)
        if status:
            filters.append(Request.status == status)
        if master_id:
            filters.append(Request.master_id == master_id)
        if date_from:
            filters.append(Request.created_at >= date_from)
        if date_to:
            filters.append(Request.created_at <= date_to)
        if phone_filter:
            filters.append(Request.client_phone.like(f"%{phone_filter}%"))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Сортировка по индексированному полю
        query = query.order_by(desc(Request.created_at))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.unique().scalars().all())
    
    @staticmethod
    @performance_monitor
    async def get_request_by_id_optimized(db: AsyncSession, request_id: int) -> Optional[Request]:
        """Оптимизированное получение заявки по ID"""
        query = select(Request).options(
            joinedload(Request.city),
            joinedload(Request.request_type),
            joinedload(Request.advertising_campaign),
            joinedload(Request.direction),
            joinedload(Request.master).joinedload(Master.city),
            selectinload(Request.files)
        ).where(Request.id == request_id)
        
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    @performance_monitor
    async def find_duplicate_requests_optimized(
        db: AsyncSession,
        client_phone: str,
        time_window_minutes: int = 30
    ) -> List[Request]:
        """
        Оптимизированный поиск дубликатов заявок
        Использует специальный индекс для быстрого поиска
        """
        time_threshold = datetime.now() - timedelta(minutes=time_window_minutes)
        
        query = select(Request).where(
            and_(
                Request.client_phone == client_phone,
                Request.created_at >= time_threshold
            )
        ).order_by(desc(Request.created_at))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    @performance_monitor
    async def get_callcenter_statistics_optimized(
        db: AsyncSession,
        city_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Оптимизированная статистика для колл-центра
        Использует агрегированные запросы вместо загрузки всех записей
        """
        # Базовые фильтры
        filters = []
        if city_id:
            filters.append(Request.city_id == city_id)
        if date_from:
            filters.append(Request.created_at >= date_from)
        if date_to:
            filters.append(Request.created_at <= date_to)
        
        base_filter = and_(*filters) if filters else text("1=1")
        
        # Агрегированные запросы для статистики
        queries = [
            # Общее количество заявок
            select(func.count(Request.id)).where(base_filter),
            # Статистика по статусам
            select(Request.status, func.count(Request.id)).where(base_filter).group_by(Request.status),
            # Статистика по городам
            select(City.name, func.count(Request.id))
            .select_from(Request.join(City))
            .where(base_filter)
            .group_by(City.name),
            # Статистика по типам заявок
            select(RequestType.name, func.count(Request.id))
            .select_from(Request.join(RequestType))
            .where(base_filter)
            .group_by(RequestType.name)
        ]
        
        # Выполняем все запросы параллельно
        results = await asyncio.gather(*[db.execute(query) for query in queries])
        
        total_count = results[0].scalar()
        status_stats = {row[0]: row[1] for row in results[1].fetchall()}
        city_stats = {row[0]: row[1] for row in results[2].fetchall()}
        type_stats = {row[0]: row[1] for row in results[3].fetchall()}
        
        return {
            "total_requests": total_count,
            "status_distribution": status_stats,
            "city_distribution": city_stats,
            "type_distribution": type_stats,
            "conversion_rate": round(
                (status_stats.get("done", 0) / total_count * 100) if total_count > 0 else 0, 2
            )
        }
    
    # === ТРАНЗАКЦИИ (оптимизированные запросы) ===
    
    @staticmethod
    @performance_monitor
    async def get_transactions_optimized(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        city_id: Optional[int] = None,
        transaction_type_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None
    ) -> List[Transaction]:
        """Оптимизированное получение транзакций с фильтрацией"""
        query = select(Transaction).options(
            joinedload(Transaction.city),
            joinedload(Transaction.transaction_type),
            selectinload(Transaction.files)
        )
        
        filters = []
        if city_id:
            filters.append(Transaction.city_id == city_id)
        if transaction_type_id:
            filters.append(Transaction.transaction_type_id == transaction_type_id)
        if date_from:
            filters.append(Transaction.specified_date >= date_from)
        if date_to:
            filters.append(Transaction.specified_date <= date_to)
        if amount_min is not None:
            filters.append(Transaction.amount >= amount_min)
        if amount_max is not None:
            filters.append(Transaction.amount <= amount_max)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(Transaction.specified_date))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.unique().scalars().all())
    
    @staticmethod
    @performance_monitor
    async def get_financial_summary_optimized(
        db: AsyncSession,
        city_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Оптимизированная финансовая сводка"""
        filters = []
        if city_id:
            filters.append(Transaction.city_id == city_id)
        if date_from:
            filters.append(Transaction.specified_date >= date_from)
        if date_to:
            filters.append(Transaction.specified_date <= date_to)
        
        base_filter = and_(*filters) if filters else text("1=1")
        
        # Агрегированные запросы
        queries = [
            # Общая сумма транзакций
            select(func.sum(Transaction.amount)).where(base_filter),
            # Количество транзакций
            select(func.count(Transaction.id)).where(base_filter),
            # Средняя сумма транзакции
            select(func.avg(Transaction.amount)).where(base_filter),
            # Сумма по типам транзакций
            select(TransactionType.name, func.sum(Transaction.amount))
            .select_from(Transaction.join(TransactionType))
            .where(base_filter)
            .group_by(TransactionType.name)
        ]
        
        results = await asyncio.gather(*[db.execute(query) for query in queries])
        
        total_amount = results[0].scalar() or 0
        total_count = results[1].scalar() or 0
        avg_amount = results[2].scalar() or 0
        type_amounts = {row[0]: float(row[1]) for row in results[3].fetchall()}
        
        return {
            "total_amount": float(total_amount),
            "total_count": total_count,
            "average_amount": float(avg_amount),
            "by_type": type_amounts
        }
    
    # === УТИЛИТЫ ===
    
    @staticmethod
    async def invalidate_cache_patterns(patterns: List[str]):
        """Инвалидация кеша по паттернам"""
        for pattern in patterns:
            await cache_manager.clear_pattern(pattern)
    
    @staticmethod
    async def warm_up_cache(db: AsyncSession):
        """Прогрев кеша популярными запросами"""
        try:
            # Загружаем справочники
            await OptimizedCRUDv2.get_cities_cached(db)
            await OptimizedCRUDv2.get_request_types_cached(db)
            await OptimizedCRUDv2.get_directions_cached(db)
            await OptimizedCRUDv2.get_advertising_campaigns_cached(db)
            
            # Загружаем мастеров по основным городам
            cities_result = await db.execute(select(City.id).limit(5))
            city_ids = [row[0] for row in cities_result.fetchall()]
            
            for city_id in city_ids:
                await OptimizedCRUDv2.get_masters_by_city_cached(db, city_id)
            
            logger.info("Кеш прогрет успешно")
            
        except Exception as e:
            logger.error(f"Ошибка прогрева кеша: {e}")


# Глобальный экземпляр для использования в API
optimized_crud = OptimizedCRUDv2() 