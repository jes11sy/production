#!/usr/bin/env python3
"""
Скрипт для запуска приложения с поддержкой HTTPS в development окружении
"""
import uvicorn
import logging
from app.ssl_config import create_self_signed_cert, get_ssl_context

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска"""
    try:
        # Создаем самоподписанный сертификат для development
        cert_file, key_file = create_self_signed_cert()
        
        # Создаем SSL контекст
        ssl_context = get_ssl_context(cert_file, key_file)
        
        logger.info("🚀 Запуск сервера с HTTPS...")
        logger.info("📍 HTTPS: https://localhost:8443")
        logger.info("📍 HTTP: http://localhost:8000 (редирект на HTTPS)")
        logger.info("📖 Документация: https://localhost:8443/docs")
        logger.info("⚠️  Самоподписанный сертификат - браузер покажет предупреждение")
        
        # Запускаем сервер с HTTPS
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8443,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
            reload=True,
            reload_dirs=["app"],
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска HTTPS сервера: {e}")
        logger.info("💡 Fallback: запуск обычного HTTP сервера...")
        
        # Fallback на HTTP
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app"],
            log_level="info"
        )

if __name__ == "__main__":
    main() 