import asyncio
from app.database import engine
from app.models import Request
from sqlalchemy import select

async def check_request():
    async with engine.begin() as conn:
        result = await conn.execute(select(Request).where(Request.id == 2))
        request = result.scalar_one_or_none()
        if request:
            print(f'Заявка с ID 2 найдена:')
            print(f'  ID: {request.id}')
            print(f'  Клиент: {request.client_name}')
            print(f'  Телефон: {request.client_phone}')
            print(f'  Статус: {request.status}')
            print(f'  Город ID: {request.city_id}')
            print(f'  Тип заявки ID: {request.request_type_id}')
            print(f'  Направление ID: {request.direction_id}')
            print(f'  РК ID: {request.advertising_campaign_id}')
            print(f'  Адрес: {request.address}')
            print(f'  Дата встречи: {request.meeting_date}')
            print(f'  Проблема: {request.problem}')
            print(f'  Номер АТС: {request.ats_number}')
            print(f'  Имя КЦ: {request.call_center_name}')
            print(f'  Заметка КЦ: {request.call_center_notes}')
        else:
            print('Заявка с ID 2 не найдена')

if __name__ == "__main__":
    asyncio.run(check_request()) 