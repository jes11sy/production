from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.auth import require_admin, require_director, require_manager, require_callcenter
from ..core.crud import (
    create_master, get_master, update_master,
    create_employee, get_employee, update_employee,
    create_administrator, get_administrator, update_administrator,
    get_cities, get_roles
)
from ..core.optimized_crud import OptimizedUserCRUD
from ..core.schemas import (
    MasterCreate, MasterUpdate, MasterResponse,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    AdministratorCreate, AdministratorUpdate, AdministratorResponse,
    CityResponse, RoleResponse
)
from ..core.models import Master, Employee, Administrator, City
from ..core.cors_utils import create_cors_response, get_cors_headers
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/users", tags=["users"])

# Роуты для мастеров
@router.post("/masters/", response_model=MasterResponse)
async def create_new_master(
    master: MasterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Создание нового мастера"""
    return await create_master(db=db, master=master)


@router.get("/masters/")
async def read_masters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Получение списка мастеров (временно упрощенная версия)"""
    # Временно возвращаем простые словари, минуя Pydantic валидацию
    query = select(Master).options(
        selectinload(Master.city)
    ).offset(skip).limit(limit).order_by(Master.created_at.desc())
    
    result = await db.execute(query)
    masters = result.scalars().all()
    
    # Преобразуем в простые словари
    masters_data = []
    for master in masters:
        masters_data.append({
            "id": master.id,
            "full_name": master.full_name,
            "phone_number": master.phone_number,
            "status": master.status,
            "city": {"id": master.city.id, "name": master.city.name} if master.city else None,
            "created_at": master.created_at.isoformat() if master.created_at is not None else None,
            "birth_date": master.birth_date.isoformat() if master.birth_date is not None else None,
            "passport": master.passport,
            "chat_id": master.chat_id,
            "login": master.login,
            "notes": master.notes
        })
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(content=masters_data, headers=cors_headers)


@router.get("/masters/{master_id}")
async def read_master(
    master_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Получение конкретного мастера"""
    master = await get_master(db=db, master_id=master_id)
    if master is None:
        raise HTTPException(status_code=404, detail="Master not found")
    return master


@router.put("/masters/{master_id}")
async def update_master_data(
    master_id: int,
    master: MasterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Обновление данных мастера"""
    updated_master = await update_master(db=db, master_id=master_id, master=master)
    if updated_master is None:
        raise HTTPException(status_code=404, detail="Master not found")
    return updated_master


@router.delete("/masters/{master_id}")
async def delete_master(
    master_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Удаление мастера (только для администраторов)"""
    # Проверяем существование мастера
    query = select(Master).where(Master.id == master_id)
    result = await db.execute(query)
    master = result.scalar_one_or_none()
    
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    
    # Проверяем, что у мастера нет активных заявок
    from ..core.models import Request
    requests_query = select(Request).where(
        Request.master_id == master_id,
        Request.status.in_(["new", "in_progress", "pending"])
    )
    requests_result = await db.execute(requests_query)
    active_requests = requests_result.scalars().all()
    
    if active_requests:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete master with active requests"
        )
    
    # Удаляем мастера
    await db.delete(master)
    await db.commit()
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(
        content={"message": "Master deleted successfully"},
        headers=cors_headers
    )


# Роуты для сотрудников
@router.post("/employees/", response_model=EmployeeResponse)
async def create_new_employee(
    employee: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Создание нового сотрудника"""
    return await create_employee(db=db, employee=employee)


@router.options("/employees/")
async def employees_options():
    """Handle preflight requests for employees endpoint"""
    return create_cors_response(allowed_methods="GET, POST, PUT, DELETE, OPTIONS")

@router.get("/employees/")
async def read_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Получение списка сотрудников (оптимизированная версия)"""
    # Используем оптимизированный запрос с предзагрузкой связей
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    
    query = select(Employee).options(
        joinedload(Employee.role),
        joinedload(Employee.city)
    ).offset(skip).limit(limit).order_by(Employee.created_at.desc())
    
    result = await db.execute(query)
    employees = list(result.unique().scalars().all())
    
    # Преобразуем в простые словари
    employees_data = []
    for employee in employees:
        employee_dict = {
            "id": employee.id,
            "name": employee.name,
            "role_id": employee.role_id,
            "status": employee.status,
            "login": employee.login,
            "notes": employee.notes,
            "created_at": employee.created_at.isoformat() if employee.created_at is not None else None,
            "role": {"id": employee.role.id, "name": employee.role.name} if employee.role else None,
            "city": {"id": employee.city.id, "name": employee.city.name} if employee.city else None
        }
        employees_data.append(employee_dict)
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(content=employees_data, headers=cors_headers)


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def read_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Получение сотрудника по ID"""
    employee = await get_employee(db=db, employee_id=employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_existing_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_director)
):
    """Обновление сотрудника"""
    updated_employee = await update_employee(db=db, employee_id=employee_id, employee=employee)
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated_employee


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Удаление сотрудника (только для администраторов)"""
    # Проверяем существование сотрудника
    query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Проверяем, что это не последний администратор
    if employee.role and employee.role.name == "admin":
        admin_count_query = select(Employee).join(Employee.role).where(
            Employee.role.has(name="admin"),
            Employee.id != employee_id
        )
        admin_count_result = await db.execute(admin_count_query)
        remaining_admins = admin_count_result.scalars().all()
        
        if len(remaining_admins) == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last administrator"
            )
    
    # Удаляем сотрудника
    await db.delete(employee)
    await db.commit()
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(content={"message": "Employee deleted successfully"}, headers=cors_headers)


# Роуты для администраторов
@router.post("/administrators/", response_model=AdministratorResponse)
async def create_new_administrator(
    administrator: AdministratorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Создание нового администратора"""
    return await create_administrator(db=db, administrator=administrator)


@router.options("/administrators/")
async def administrators_options():
    """Handle preflight requests for administrators endpoint"""
    return create_cors_response(allowed_methods="GET, POST, PUT, DELETE, OPTIONS")

@router.get("/administrators/")
async def read_administrators(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Получение списка администраторов (оптимизированная версия)"""
    # Используем оптимизированный запрос с предзагрузкой связей
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    
    query = select(Administrator).options(
        joinedload(Administrator.role)
    ).offset(skip).limit(limit).order_by(Administrator.created_at.desc())
    
    result = await db.execute(query)
    administrators = list(result.unique().scalars().all())
    
    # Преобразуем в простые словари
    administrators_data = []
    for admin in administrators:
        admin_dict = {
            "id": admin.id,
            "name": admin.name,
            "role_id": admin.role_id,
            "status": admin.status,
            "login": admin.login,
            "notes": admin.notes,
            "created_at": admin.created_at.isoformat() if admin.created_at is not None else None,
            "role": {"id": admin.role.id, "name": admin.role.name} if admin.role else None
        }
        administrators_data.append(admin_dict)
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(content=administrators_data, headers=cors_headers)


@router.get("/administrators/{administrator_id}", response_model=AdministratorResponse)
async def read_administrator(
    administrator_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Получение администратора по ID"""
    administrator = await get_administrator(db=db, administrator_id=administrator_id)
    if administrator is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    return administrator


@router.put("/administrators/{administrator_id}", response_model=AdministratorResponse)
async def update_existing_administrator(
    administrator_id: int,
    administrator: AdministratorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Обновление администратора"""
    updated_administrator = await update_administrator(db=db, administrator_id=administrator_id, administrator=administrator)
    if updated_administrator is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    return updated_administrator


@router.delete("/administrators/{administrator_id}")
async def delete_administrator(
    administrator_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Удаление администратора (только для других администраторов)"""
    # Проверяем существование администратора
    query = select(Administrator).where(Administrator.id == administrator_id)
    result = await db.execute(query)
    administrator = result.scalar_one_or_none()
    
    if not administrator:
        raise HTTPException(status_code=404, detail="Administrator not found")
    
    # Нельзя удалять самого себя
    if administrator_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete yourself"
        )
    
    # Проверяем, что это не последний администратор
    admin_count_query = select(Administrator).where(Administrator.id != administrator_id)
    admin_count_result = await db.execute(admin_count_query)
    remaining_admins = admin_count_result.scalars().all()
    
    if len(remaining_admins) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the last administrator"
        )
    
    # Удаляем администратора
    await db.delete(administrator)
    await db.commit()
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(content={"message": "Administrator deleted successfully"}, headers=cors_headers)


# Дополнительные эндпоинты для получения справочных данных
@router.options("/cities/")
async def cities_options():
    """Handle preflight requests for cities endpoint"""
    return create_cors_response(allowed_methods="GET, POST, PUT, DELETE, OPTIONS")

@router.get("/cities/")
async def get_cities_list(
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_callcenter)
):
    """Получение списка городов"""
    # Получаем города из базы данных
    result = await db.execute(select(City))
    cities = result.scalars().all()
    
    # Преобразуем в простые словари
    cities_data = [{"id": city.id, "name": city.name} for city in cities]
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(content=cities_data, headers=cors_headers)


@router.options("/roles/")
async def roles_options():
    """Handle preflight requests for roles endpoint"""
    return create_cors_response(allowed_methods="GET, POST, PUT, DELETE, OPTIONS")

@router.get("/roles/")
async def get_roles_list(
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_manager)
):
    """Получение списка ролей"""
    # Получаем роли из базы данных
    from sqlalchemy import select
    from ..core.models import Role
    
    result = await db.execute(select(Role))
    roles = result.scalars().all()
    
    # Преобразуем в простые словари
    roles_data = [{"id": role.id, "name": role.name} for role in roles]
    
    cors_headers = get_cors_headers("GET, POST, PUT, DELETE, OPTIONS")
    return JSONResponse(content=roles_data, headers=cors_headers) 