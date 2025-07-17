from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core import crud, schemas
from datetime import datetime
import logging
import json
import urllib.parse

router = APIRouter()

@router.post("/webhook")
async def mango_webhook_root(request: Request, db: AsyncSession = Depends(get_db)):
    return await mango_webhook(request, db)

@router.post("/webhook/{subpath:path}")
async def mango_webhook(request: Request, db: AsyncSession = Depends(get_db), subpath: str = ""):
    # Логируем сырое тело
    raw_body = await request.body()
    logging.warning(f"MANGO RAW BODY: {raw_body}")

    # Пробуем получить form-data и распарсить JSON
    try:
        form = await request.form()
        json_str = form.get("json")
        if json_str and isinstance(json_str, str):
            json_str = urllib.parse.unquote_plus(json_str)
            data = json.loads(json_str)
        else:
            data = {}
    except Exception as e:
        logging.warning(f"FORM PARSE ERROR: {e}")
        data = {}

    logging.warning(f"MANGO PARSED DATA: {data}")

    # Дальше — твоя логика: ищем from/to, создаём заявку и т.д.
    # В Mango Office from и to — это объекты, а не строки!
    from_number = data.get("from", {}).get("number")
    to_number = data.get("to", {}).get("number")
    
    # Логируем дополнительную информацию для отладки
    call_id = data.get("call_id")
    seq = data.get("seq")
    call_state = data.get("call_state")
    logging.warning(f"MANGO CALL INFO: CallID={call_id}, Seq={seq}, State={call_state}, From={from_number}, To={to_number}")
    
    if not from_number or not to_number:
        return {"ok": True}

    # Получаем номер, на который позвонили (line_number)
    phone_number = None
    if 'to' in data and isinstance(data['to'], dict):
        phone_number = data['to'].get('line_number')
    if not phone_number:
        return {"ok": True, "detail": "Нет номера для поиска РК"}

    # СТРОГАЯ ПРОВЕРКА на дубликаты заявок
    existing = await crud.get_existing_new_request_by_phone(db, from_number)
    if existing:
        logging.warning(f"MANGO DUPLICATE BLOCKED: Phone {from_number}, existing request ID {existing.id}, created at {existing.created_at}")
        return {"ok": True, "detail": f"Заявка уже существует (ID: {existing.id})"}

    # Найти рекламную кампанию по номеру
    campaign = await crud.get_advertising_campaign_by_phone(db, phone_number)
    if not campaign:
        return {"ok": True, "detail": "Не найдена РК для номера"}

    city_id = campaign.city_id

    # Определяем тип заявки: 'Впервые' или 'Повтор'
    # ВАЖНО: Проверяем ВСЕ заявки, не только за последние 30 минут
    is_first_time = await crud.check_client_first_time(db, from_number)
    if is_first_time:
        request_type = await crud.get_request_type_by_name(db, "Впервые")
        logging.warning(f"MANGO TYPE DECISION: Phone {from_number} - FIRST TIME (Впервые)")
    else:
        request_type = await crud.get_request_type_by_name(db, "Повтор")
        logging.warning(f"MANGO TYPE DECISION: Phone {from_number} - REPEAT (Повтор)")
    request_type_id = request_type.id if request_type else None

    # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА перед созданием
    final_check = await crud.get_existing_new_request_by_phone(db, from_number)
    if final_check:
        logging.warning(f"MANGO FINAL CHECK BLOCKED: Phone {from_number}, existing request ID {final_check.id}")
        return {"ok": True, "detail": f"Заявка уже существует (финальная проверка, ID: {final_check.id})"}
    
    request_in = schemas.RequestCreate(
        advertising_campaign_id=campaign.id,
        city_id=campaign.city_id,
        request_type_id=request_type_id,
        client_phone=from_number,
        status="Новая",
        ats_number=phone_number,
        result=None,
        call_center_name=None,
        avito_chat_id=None
    )
    
    try:
        new_request = await crud.create_request(db, request_in)
        request_type_name = request_type.name if request_type else "Unknown"
        
        logging.warning(f"MANGO REQUEST CREATED: Phone {from_number}, Type: {request_type_name}, ID: {new_request.id}, Campaign: {campaign.name}")
        
        return {"ok": True, "request_id": new_request.id, "type": request_type_name}
    except Exception as e:
        logging.error(f"MANGO REQUEST CREATION ERROR: Phone {from_number}, Error: {e}")
        # Возможно, заявка уже была создана другим процессом
        await db.rollback()
        return {"ok": True, "detail": f"Ошибка создания заявки: {str(e)}"} 