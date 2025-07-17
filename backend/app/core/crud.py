from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
import logging
from .models import (
    City, RequestType, Direction, Role, TransactionType,
    AdvertisingCampaign, Master, Employee, Administrator,
    Request, Transaction, File
)
from .schemas import (
    CityCreate, CityUpdate, RequestTypeCreate, RequestTypeUpdate,
    DirectionCreate, DirectionUpdate, RoleCreate, RoleUpdate,
    TransactionTypeCreate, TransactionTypeUpdate,
    AdvertisingCampaignCreate, AdvertisingCampaignUpdate,
    MasterCreate, MasterUpdate, EmployeeCreate, EmployeeUpdate,
    AdministratorCreate, AdministratorUpdate,
    RequestCreate, RequestUpdate, TransactionCreate, TransactionUpdate,
    FileCreate, FileUpdate
)
from .auth import get_password_hash


# CRUD операции для городов
async def create_city(db: AsyncSession, city: CityCreate) -> City:
    db_city = City(**city.dict())
    db.add(db_city)
    await db.commit()
    await db.refresh(db_city)
    return db_city


async def get_cities(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[City]:
    result = await db.execute(select(City).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_city(db: AsyncSession, city_id: int) -> Optional[City]:
    result = await db.execute(select(City).where(City.id == city_id))
    return result.scalar_one_or_none()


async def update_city(db: AsyncSession, city_id: int, city: CityUpdate) -> Optional[City]:
    result = await db.execute(select(City).where(City.id == city_id))
    db_city = result.scalar_one_or_none()
    if db_city:
        update_data = city.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_city, field, value)
        await db.commit()
        await db.refresh(db_city)
    return db_city


async def delete_city(db: AsyncSession, city_id: int) -> bool:
    result = await db.execute(select(City).where(City.id == city_id))
    db_city = result.scalar_one_or_none()
    if db_city:
        await db.delete(db_city)
        await db.commit()
        return True
    return False


# CRUD операции для типов заявок
async def create_request_type(db: AsyncSession, request_type: RequestTypeCreate) -> RequestType:
    db_request_type = RequestType(**request_type.dict())
    db.add(db_request_type)
    await db.commit()
    await db.refresh(db_request_type)
    return db_request_type


async def get_request_types(db: AsyncSession) -> List[RequestType]:
    result = await db.execute(select(RequestType))
    return list(result.scalars().all())


async def get_request_type(db: AsyncSession, request_type_id: int) -> Optional[RequestType]:
    result = await db.execute(select(RequestType).where(RequestType.id == request_type_id))
    return result.scalar_one_or_none()


async def get_request_type_by_name(db, name: str):
    from .models import RequestType
    from sqlalchemy.future import select
    result = await db.execute(select(RequestType).where(RequestType.name == name))
    return result.scalars().first()


# CRUD операции для направлений
async def create_direction(db: AsyncSession, direction: DirectionCreate) -> Direction:
    db_direction = Direction(**direction.dict())
    db.add(db_direction)
    await db.commit()
    await db.refresh(db_direction)
    return db_direction


async def get_directions(db: AsyncSession) -> List[Direction]:
    result = await db.execute(select(Direction))
    return list(result.scalars().all())


async def get_direction(db: AsyncSession, direction_id: int) -> Optional[Direction]:
    result = await db.execute(select(Direction).where(Direction.id == direction_id))
    return result.scalar_one_or_none()


# CRUD операции для ролей
async def create_role(db: AsyncSession, role: RoleCreate) -> Role:
    db_role = Role(**role.dict())
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role


async def get_roles(db: AsyncSession) -> List[Role]:
    result = await db.execute(select(Role))
    return list(result.scalars().all())


# CRUD операции для типов транзакций
async def create_transaction_type(db: AsyncSession, transaction_type: TransactionTypeCreate) -> TransactionType:
    db_transaction_type = TransactionType(**transaction_type.dict())
    db.add(db_transaction_type)
    await db.commit()
    await db.refresh(db_transaction_type)
    return db_transaction_type


async def get_transaction_types(db: AsyncSession) -> List[TransactionType]:
    result = await db.execute(select(TransactionType))
    return list(result.scalars().all())


# CRUD операции для рекламных кампаний
async def create_advertising_campaign(db: AsyncSession, campaign: AdvertisingCampaignCreate) -> AdvertisingCampaign:
    db_campaign = AdvertisingCampaign(**campaign.dict())
    db.add(db_campaign)
    await db.commit()
    await db.refresh(db_campaign)
    # Получить с подгруженным city
    result = await db.execute(
        select(AdvertisingCampaign)
        .options(selectinload(AdvertisingCampaign.city))
        .where(AdvertisingCampaign.id == db_campaign.id)
    )
    return result.scalar_one()


async def get_advertising_campaigns(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[AdvertisingCampaign]:
    result = await db.execute(
        select(AdvertisingCampaign)
        .options(selectinload(AdvertisingCampaign.city))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_advertising_campaign(db: AsyncSession, campaign_id: int) -> Optional[AdvertisingCampaign]:
    result = await db.execute(
        select(AdvertisingCampaign)
        .options(selectinload(AdvertisingCampaign.city))
        .where(AdvertisingCampaign.id == campaign_id)
    )
    return result.scalar_one_or_none()


async def update_advertising_campaign(db: AsyncSession, campaign_id: int, campaign: AdvertisingCampaignUpdate) -> Optional[AdvertisingCampaign]:
    result = await db.execute(select(AdvertisingCampaign).where(AdvertisingCampaign.id == campaign_id))
    db_campaign = result.scalar_one_or_none()
    if db_campaign:
        update_data = campaign.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_campaign, field, value)
        await db.commit()
        await db.refresh(db_campaign)
    return db_campaign


async def get_advertising_campaign_by_phone(db, phone_number: str):
    result = await db.execute(
        select(AdvertisingCampaign).where(AdvertisingCampaign.phone_number == phone_number)
    )
    return result.scalars().first()


# CRUD операции для мастеров
async def create_master(db: AsyncSession, master: MasterCreate) -> Master:
    master_data = master.dict()
    password = master_data.pop("password")
    master_data["password_hash"] = get_password_hash(password)
    
    db_master = Master(**master_data)
    db.add(db_master)
    await db.commit()
    await db.refresh(db_master)
    # ВАЖНО: получить мастера с подгруженной связью city
    result = await db.execute(
        select(Master).options(selectinload(Master.city)).where(Master.id == db_master.id)
    )
    return result.scalar_one()


async def get_masters(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Master]:
    result = await db.execute(
        select(Master)
        .options(selectinload(Master.city))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_master(db: AsyncSession, master_id: int) -> Optional[Master]:
    result = await db.execute(
        select(Master)
        .options(selectinload(Master.city))
        .where(Master.id == master_id)
    )
    return result.scalar_one_or_none()


async def update_master(db: AsyncSession, master_id: int, master: MasterUpdate) -> Optional[Master]:
    result = await db.execute(select(Master).where(Master.id == master_id))
    db_master = result.scalar_one_or_none()
    if db_master:
        update_data = master.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_master, field, value)
        await db.commit()
        await db.refresh(db_master)
    return db_master


# CRUD операции для сотрудников
async def create_employee(db: AsyncSession, employee: EmployeeCreate) -> Employee:
    employee_data = employee.dict()
    password = employee_data.pop("password")
    employee_data["password_hash"] = get_password_hash(password)
    
    db_employee = Employee(**employee_data)
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee


async def get_employees(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Employee]:
    result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.role), selectinload(Employee.city))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_employee(db: AsyncSession, employee_id: int) -> Optional[Employee]:
    result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.role), selectinload(Employee.city))
        .where(Employee.id == employee_id)
    )
    return result.scalar_one_or_none()


async def update_employee(db: AsyncSession, employee_id: int, employee: EmployeeUpdate) -> Optional[Employee]:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    db_employee = result.scalar_one_or_none()
    if db_employee:
        update_data = employee.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_employee, field, value)
        await db.commit()
        await db.refresh(db_employee)
    return db_employee


# CRUD операции для администраторов
async def create_administrator(db: AsyncSession, administrator: AdministratorCreate) -> Administrator:
    admin_data = administrator.dict()
    password = admin_data.pop("password")
    admin_data["password_hash"] = get_password_hash(password)
    
    db_administrator = Administrator(**admin_data)
    db.add(db_administrator)
    await db.commit()
    await db.refresh(db_administrator)
    return db_administrator


async def get_administrators(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Administrator]:
    result = await db.execute(
        select(Administrator)
        .options(selectinload(Administrator.role))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_administrator(db: AsyncSession, administrator_id: int) -> Optional[Administrator]:
    result = await db.execute(
        select(Administrator)
        .options(selectinload(Administrator.role))
        .where(Administrator.id == administrator_id)
    )
    return result.scalar_one_or_none()


async def update_administrator(db: AsyncSession, administrator_id: int, administrator: AdministratorUpdate) -> Optional[Administrator]:
    result = await db.execute(select(Administrator).where(Administrator.id == administrator_id))
    db_administrator = result.scalar_one_or_none()
    if db_administrator:
        update_data = administrator.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_administrator, field, value)
        await db.commit()
        await db.refresh(db_administrator)
    return db_administrator


# CRUD операции для заявок
async def create_request(db: AsyncSession, request: RequestCreate) -> Request:
    db_request = Request(**request.dict())
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    # Получить с подгруженными связанными данными
    result = await db.execute(
        select(Request)
        .options(
            selectinload(Request.advertising_campaign),
            selectinload(Request.city),
            selectinload(Request.request_type),
            selectinload(Request.direction),
            selectinload(Request.master),
            selectinload(Request.files)
        )
        .where(Request.id == db_request.id)
    )
    return result.scalar_one()


async def get_requests(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Request]:
    result = await db.execute(
        select(Request)
        .options(
            selectinload(Request.advertising_campaign),
            selectinload(Request.city),
            selectinload(Request.request_type),
            selectinload(Request.direction),
            selectinload(Request.master),
            selectinload(Request.files),
        )
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_request(db: AsyncSession, request_id: int) -> Optional[Request]:
    result = await db.execute(
        select(Request)
        .options(
            selectinload(Request.advertising_campaign),
            selectinload(Request.city),
            selectinload(Request.request_type),
            selectinload(Request.direction),
            selectinload(Request.master),
            selectinload(Request.files)
        )
        .where(Request.id == request_id)
    )
    return result.scalar_one_or_none()


async def update_request(db: AsyncSession, request_id: int, request: RequestUpdate) -> Optional[Request]:
    import logging
    logger = logging.getLogger(__name__)
    
    result = await db.execute(select(Request).where(Request.id == request_id))
    db_request = result.scalar_one_or_none()
    if db_request:
        old_status = db_request.status  # Сохраняем старый статус
        logger.info(f"🔍 CRUD: Текущий статус заявки {request_id}: {old_status}")
        
        update_data = request.dict(exclude_unset=True)
        logger.info(f"📝 CRUD: Данные для обновления: {update_data}")
        
        for field, value in update_data.items():
            logger.info(f"🔧 CRUD: Устанавливаем {field} = {value}")
            setattr(db_request, field, value)
        
        logger.info(f"💾 CRUD: Статус после setattr: {db_request.status}")
        await db.commit()
        logger.info(f"✅ CRUD: Коммит выполнен")
        await db.refresh(db_request)
        logger.info(f"🔄 CRUD: Статус после refresh: {db_request.status}")

        # === Бизнес-логика по транзакциям ===
        # Временно отключена из-за ошибок типизации
        # TODO: Исправить логику создания транзакций
        # try:
        #     # Получаем id типа транзакции "Приход"
        #     from .models import Transaction, TransactionType
        #     transaction_type_result = await db.execute(select(TransactionType).where(TransactionType.name == "Приход"))
        #     transaction_type = transaction_type_result.scalar_one_or_none()
        #     if transaction_type is not None:
        #         # ... логика создания транзакций
        # except Exception as e:
        #     logger.error(f"Error in transaction business logic for request {request_id}: {e}")
        await db.commit()
        logger.info(f"🔒 CRUD: Финальный коммит выполнен")
        # === END бизнес-логика ===
        
        # Получить обновленную заявку с подгруженными связанными данными
        result = await db.execute(
            select(Request)
            .options(
                selectinload(Request.advertising_campaign),
                selectinload(Request.city),
                selectinload(Request.request_type),
                selectinload(Request.direction),
                selectinload(Request.master),
                selectinload(Request.files)
            )
            .where(Request.id == request_id)
        )
        final_request = result.scalar_one_or_none()
        logger.info(f"🎯 CRUD: Финальный статус заявки {request_id}: {final_request.status if final_request else 'None'}")
        return final_request
    return None


async def delete_request(db: AsyncSession, request_id: int) -> bool:
    result = await db.execute(select(Request).where(Request.id == request_id))
    db_request = result.scalar_one_or_none()
    if db_request:
        await db.delete(db_request)
        await db.commit()
        return True
    return False


# CRUD операции для транзакций
async def create_transaction(db: AsyncSession, transaction: TransactionCreate) -> Transaction:
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    # Получить с подгруженными связанными данными
    result = await db.execute(
        select(Transaction)
        .options(
            selectinload(Transaction.city),
            selectinload(Transaction.transaction_type),
            selectinload(Transaction.files)
        )
        .where(Transaction.id == db_transaction.id)
    )
    return result.scalar_one()


async def get_transactions(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Transaction]:
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.city), selectinload(Transaction.transaction_type), selectinload(Transaction.files))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_transaction(db: AsyncSession, transaction_id: int) -> Optional[Transaction]:
    result = await db.execute(
        select(Transaction)
        .options(
            selectinload(Transaction.city),
            selectinload(Transaction.transaction_type),
            selectinload(Transaction.files)
        )
        .where(Transaction.id == transaction_id)
    )
    return result.scalar_one_or_none()


async def update_transaction(db: AsyncSession, transaction_id: int, transaction: TransactionUpdate) -> Optional[Transaction]:
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = result.scalar_one_or_none()
    if db_transaction:
        update_data = transaction.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_transaction, field, value)
        await db.commit()
        await db.refresh(db_transaction)
        
        # Получить обновленную транзакцию с подгруженными связанными данными
        result = await db.execute(
            select(Transaction)
            .options(
                selectinload(Transaction.city),
                selectinload(Transaction.transaction_type),
                selectinload(Transaction.files)
            )
            .where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()
    return None


async def delete_transaction(db: AsyncSession, transaction_id: int) -> bool:
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = result.scalar_one_or_none()
    if db_transaction:
        await db.delete(db_transaction)
        await db.commit()
        return True
    return False


# CRUD операции для файлов
async def create_file(db: AsyncSession, file: FileCreate) -> File:
    db_file = File(**file.dict())
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file


async def get_files(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[File]:
    result = await db.execute(select(File).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_file(db: AsyncSession, file_id: int) -> Optional[File]:
    result = await db.execute(
        select(File)
        .options(selectinload(File.request), selectinload(File.transaction))
        .where(File.id == file_id)
    )
    return result.scalar_one_or_none()


async def update_file(db: AsyncSession, file_id: int, file: FileUpdate) -> Optional[File]:
    result = await db.execute(select(File).where(File.id == file_id))
    db_file = result.scalar_one_or_none()
    if db_file:
        update_data = file.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_file, field, value)
        await db.commit()
        await db.refresh(db_file)
    return db_file


async def delete_file(db: AsyncSession, file_id: int) -> bool:
    result = await db.execute(select(File).where(File.id == file_id))
    db_file = result.scalar_one_or_none()
    if db_file:
        await db.delete(db_file)
        await db.commit()
        return True
    return False 

async def get_existing_new_request_by_phone(db, client_phone: str):
    from .models import Request
    from sqlalchemy.future import select
    from datetime import datetime, timedelta
    
    # СТРОГАЯ ЗАЩИТА: Проверяем любые заявки за последние 30 минут
    # Это защитит от множественных вызовов webhook'а от Mango Office
    thirty_minutes_ago = datetime.now() - timedelta(minutes=30)
    
    result = await db.execute(
        select(Request)
        .where(Request.client_phone == client_phone)
        .where(Request.created_at >= thirty_minutes_ago)
        .order_by(Request.created_at.desc())
    )
    return result.scalars().first() 

async def check_client_first_time(db, client_phone: str):
    from .models import Request
    from sqlalchemy.future import select
    result = await db.execute(select(Request).where(Request.client_phone == client_phone))
    return result.scalars().first() is None


async def link_recording_to_request(db, recording_info: dict):
    """Связывание записи звонка с заявкой по номеру телефона"""
    from .models import Request
    from sqlalchemy.future import select
    from datetime import timedelta
    
    try:
        from_number = recording_info.get('from_number')
        to_number = recording_info.get('to_number')
        call_datetime = recording_info.get('call_datetime')
        relative_path = recording_info.get('relative_path')
        
        if not from_number or not call_datetime or not relative_path:
            return None
        
        # Ищем заявку по номеру телефона в окне ±30 минут от времени звонка
        time_window = timedelta(minutes=30)
        start_time = call_datetime - time_window
        end_time = call_datetime + time_window
        
        # Сначала ищем по номеру звонящего
        result = await db.execute(
            select(Request)
            .where(Request.client_phone == from_number)
            .where(Request.created_at >= start_time)
            .where(Request.created_at <= end_time)
            .order_by(Request.created_at.desc())
        )
        
        request = result.scalars().first()
        
        # Если не найдено, пробуем найти по номеру, на который звонили
        if not request:
            # Ищем рекламную кампанию по номеру
            from .models import AdvertisingCampaign
            campaign_result = await db.execute(
                select(AdvertisingCampaign)
                .where(AdvertisingCampaign.phone_number == to_number)
            )
            campaign = campaign_result.scalars().first()
            
            if campaign:
                # Ищем заявки по этой кампании
                result = await db.execute(
                    select(Request)
                    .where(Request.advertising_campaign_id == campaign.id)
                    .where(Request.client_phone == from_number)
                    .where(Request.created_at >= start_time)
                    .where(Request.created_at <= end_time)
                    .order_by(Request.created_at.desc())
                )
                request = result.scalars().first()
        
        if request:
            # Обновляем заявку, добавляя путь к записи
            request.recording_file_path = relative_path
            await db.commit()
            await db.refresh(request)
            
            logging.info(f"RECORDING LINKED: File {recording_info['filename']} linked to request {request.id}")
            return request
        else:
            logging.warning(f"RECORDING NOT LINKED: No request found for phone {from_number} at {call_datetime}")
            return None
            
    except Exception as e:
        logging.error(f"ERROR LINKING RECORDING: {e}")
        await db.rollback()
        return None 