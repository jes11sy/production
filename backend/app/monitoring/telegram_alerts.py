import aiohttp
import asyncio
import logging
from typing import Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_alert(service: str, message: str, thread_id: Optional[int] = None):
    """
    Отправить алерт в Telegram в отдельную тему (топик) по сервису.
    Если thread_id не указан, будет создана новая тема.
    """
    if not settings.TELEGRAM_ALERTS_ENABLED or not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram alerts disabled or not configured")
        return
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": f"🚨 <b>{service.upper()}</b>\n{message}",
        "parse_mode": "HTML"
    }
    if thread_id:
        payload["message_thread_id"] = thread_id
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as resp:
            if resp.status != 200:
                logger.error(f"Telegram alert failed: {resp.status} {await resp.text()}")
            else:
                logger.info(f"Telegram alert sent for {service}")

async def create_topic_and_alert(service: str, message: str):
    """
    Создать новую тему (топик) в чате и отправить туда алерт.
    """
    if not settings.TELEGRAM_ALERTS_ENABLED or not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram alerts disabled or not configured")
        return
    
    # Создать тему (topic) можно только через sendForumTopic (метод Telegram Bot API)
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/createForumTopic"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "name": service.capitalize()
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                thread_id = data["result"]["message_thread_id"]
                await send_telegram_alert(service, message, thread_id=thread_id)
            else:
                logger.error(f"Failed to create topic for {service}: {resp.status} {await resp.text()}\nОтправляю алерт в общий чат.")
                await send_telegram_alert(service, message) 