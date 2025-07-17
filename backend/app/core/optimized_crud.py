"""
Оптимизированные CRUD операции для максимальной производительности
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, desc, asc
from sqlalchemy.orm import selectinload, joinedload, contains_eager
from datetime import datetime, timedelta, date
import logging

from .models import (
    Request, Transaction, Master, Employee, Administrator, 
    City, RequestType, Direction, AdvertisingCampaign, TransactionType,
    File, Role
)
from .schemas import RequestCreate, RequestUpdate, TransactionCreate, TransactionUpdate
from .performance import performance_monitor

logger = logging.getLogger(__name__)

class OptimizedRequestCRUD:
    """Оптимизированные операции с заявками"""
    
    @staticmethod
    @performance_monitor
    async def get_requests_paginated(
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
        Использует составные индексы для быстрой фильтрации
        """
        query = select(Request).options(
            # Используем joinedload для many-to-one связей
            joinedload(Request.city),
            joinedload(Request.request_type),
            joinedload(Request.advertising_campaign),
            joinedload(Request.direction),
            joinedload(Request.master).joinedload(Master.city),
            # Используем selectinload для one-to-many связей
            selectinload(Request.files)
        )
        
        # Применяем фильтры (используют индексы)
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
    async def get_request_by_id(db: AsyncSession, request_id: int) -> Optional[Request]:
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
    async def find_duplicate_requests(
        db: AsyncSession,
        client_phone: str,
        time_window_minutes: int = 30
    ) -> List[Request]:
        """
        Быстрый поиск дубликатов заявок по телефону
        Использует специализированный индекс idx_requests_phone_time_window
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
    async def get_requests_by_phone_range(
        db: AsyncSession,
        client_phone: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Request]:
        """
        Поиск заявок по телефону в временном диапазоне
        Для системы записей звонков
        """
        query = select(Request).where(
            and_(
                Request.client_phone == client_phone,
                Request.created_at >= start_time,
                Request.created_at <= end_time
            )
        ).order_by(desc(Request.created_at))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    @performance_monitor
    async def get_callcenter_statistics(
        db: AsyncSession,
        city_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Оптимизированная статистика для колл-центра
        Использует агрегированные запросы с индексами
        """
        base_query = select(Request)
        
        filters = []
        if city_id:
            filters.append(Request.city_id == city_id)
        if date_from:
            filters.append(Request.created_at >= date_from)
        if date_to:
            filters.append(Request.created_at <= date_to)
        
        if filters:
            base_query = base_query.where(and_(*filters))
        
        # Агрегированная статистика по статусам
        status_stats = await db.execute(
            select(
                Request.status,
                func.count(Request.id).label('count')
            ).select_from(base_query.subquery())
            .group_by(Request.status)
        )
        
        # Статистика по городам
        city_stats = await db.execute(
            select(
                City.name,
                func.count(Request.id).label('count')
            ).select_from(
                base_query.join(City, Request.city_id == City.id).subquery()
            ).group_by(City.name)
        )
        
        return {
            "status_distribution": {row.status: row.count for row in status_stats.fetchall()},
            "city_distribution": {row.name: row.count for row in city_stats.fetchall()}
        }

class OptimizedTransactionCRUD:
    """Оптимизированные операции с транзакциями"""
    
    @staticmethod
    @performance_monitor
    async def get_transactions_paginated(
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
    async def get_financial_summary(
        db: AsyncSession,
        city_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Финансовая сводка с агрегацией"""
        base_query = select(Transaction)
        
        filters = []
        if city_id:
            filters.append(Transaction.city_id == city_id)
        if date_from:
            filters.append(Transaction.specified_date >= date_from)
        if date_to:
            filters.append(Transaction.specified_date <= date_to)
        
        if filters:
            base_query = base_query.where(and_(*filters))
        
        # Агрегированная статистика
        summary = await db.execute(
            select(
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(func.case((Transaction.amount > 0, Transaction.amount), else_=0)).label('income'),
                func.sum(func.case((Transaction.amount < 0, Transaction.amount), else_=0)).label('expenses'),
                func.count(Transaction.id).label('transaction_count')
            ).select_from(base_query.subquery())
        )
        
        result = summary.fetchone()
        if result:
            return {
                "total_amount": float(result.total_amount or 0),
                "income": float(result.income or 0),
                "expenses": float(result.expenses or 0),
                "transaction_count": result.transaction_count or 0
            }
        else:
            return {
                "total_amount": 0.0,
                "income": 0.0,
                "expenses": 0.0,
                "transaction_count": 0
            }

class OptimizedUserCRUD:
    """Оптимизированные операции с пользователями"""
    
    @staticmethod
    @performance_monitor
    async def authenticate_user_optimized(
        db: AsyncSession,
        login: str
    ) -> Optional[Any]:
        """
        Оптимизированная аутентификация пользователя
        Использует индексы по логину для быстрого поиска
        """
        # Проверяем мастеров
        master_query = select(Master).options(
            joinedload(Master.city)
        ).where(Master.login == login)
        
        result = await db.execute(master_query)
        user = result.unique().scalar_one_or_none()
        if user:
            return user
        
        # Проверяем сотрудников
        employee_query = select(Employee).options(
            joinedload(Employee.role),
            joinedload(Employee.city)
        ).where(Employee.login == login)
        
        result = await db.execute(employee_query)
        user = result.unique().scalar_one_or_none()
        if user:
            return user
        
        # Проверяем администраторов
        admin_query = select(Administrator).options(
            joinedload(Administrator.role)
        ).where(Administrator.login == login)
        
        result = await db.execute(admin_query)
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    @performance_monitor
    async def get_active_masters_by_city(
        db: AsyncSession,
        city_id: int
    ) -> List[Master]:
        """
        Получение активных мастеров по городу
        Использует составной индекс idx_masters_city_status
        """
        query = select(Master).options(
            joinedload(Master.city)
        ).where(
            and_(
                Master.city_id == city_id,
                Master.status == 'active'
            )
        ).order_by(Master.full_name)
        
        result = await db.execute(query)
        return list(result.unique().scalars().all())
    
    @staticmethod
    @performance_monitor
    async def get_active_employees_by_role(
        db: AsyncSession,
        role_id: int,
        city_id: Optional[int] = None
    ) -> List[Employee]:
        """
        Получение активных сотрудников по роли
        Использует составной индекс idx_employees_role_city
        """
        filters = [
            Employee.role_id == role_id,
            Employee.status == 'active'
        ]
        
        if city_id:
            filters.append(Employee.city_id == city_id)
        
        query = select(Employee).options(
            joinedload(Employee.role),
            joinedload(Employee.city)
        ).where(and_(*filters)).order_by(Employee.name)
        
        result = await db.execute(query)
        return list(result.unique().scalars().all())

class OptimizedReferenceCRUD:
    """Оптимизированные операции со справочниками"""
    
    @staticmethod
    @performance_monitor
    async def get_all_cities_cached(db: AsyncSession) -> List[City]:
        """Получение всех городов (кешируется)"""
        query = select(City).order_by(City.name)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    @performance_monitor
    async def get_all_request_types_cached(db: AsyncSession) -> List[RequestType]:
        """Получение всех типов заявок (кешируется)"""
        query = select(RequestType).order_by(RequestType.name)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    @performance_monitor
    async def get_all_directions_cached(db: AsyncSession) -> List[Direction]:
        """Получение всех направлений (кешируется)"""
        query = select(Direction).order_by(Direction.name)
        result = await db.execute(query)
        return list(result.scalars().all())

# Создаем экземпляры для использования
optimized_requests = OptimizedRequestCRUD()
optimized_transactions = OptimizedTransactionCRUD()
optimized_users = OptimizedUserCRUD()
optimized_references = OptimizedReferenceCRUD() 