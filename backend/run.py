import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    # Продакшн конфигурация
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not is_production,  # Отключаем reload в продакшене
        log_level="info",
        workers=1 if not is_production else 2  # Больше workers в продакшене
    ) 