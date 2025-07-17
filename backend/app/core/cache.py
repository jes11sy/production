"""
Система кеширования для оптимизации производительности
"""
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from functools import wraps
import redis.asyncio as aioredis
import asyncio
import logging
from .config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Менеджер кеширования с поддержкой Redis"""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.local_cache: Dict[str, Any] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    async def initialize(self):
        """Инициализация подключения к Redis"""
        if not settings.CACHE_ENABLED:
            logger.info("Кеширование отключено в настройках")
            return
        
        try:
            self.redis_client = aioredis.from_url(
                settings.get_redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Проверяем подключение
            await self.redis_client.ping()
            logger.info("Redis подключен успешно")
            
        except Exception as e:
            logger.warning(f"Не удалось подключиться к Redis: {e}")
            logger.info("Используется локальный кеш в памяти")
            self.redis_client = None
    
    async def close(self):
        """Закрытие подключения к Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_key(self, key: str) -> str:
        """Генерация ключа с префиксом"""
        return f"{settings.CACHE_KEY_PREFIX}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """Сериализация значения для кеширования"""
        try:
            if isinstance(value, (dict, list, str, int, float, bool)):
                return json.dumps(value, ensure_ascii=False, default=str)
            else:
                # Для сложных объектов используем pickle
                return pickle.dumps(value).hex()
        except Exception as e:
            logger.error(f"Ошибка сериализации: {e}")
            return json.dumps(str(value))
    
    def _deserialize_value(self, value: str) -> Any:
        """Десериализация значения из кеша"""
        try:
            # Сначала пробуем JSON
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                # Если не JSON, то pickle
                return pickle.loads(bytes.fromhex(value))
            except Exception as e:
                logger.error(f"Ошибка десериализации: {e}")
                return value
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кеша"""
        cache_key = self._generate_key(key)
        
        try:
            if self.redis_client:
                value = await self.redis_client.get(cache_key)
                if value is not None:
                    self.cache_stats["hits"] += 1
                    return self._deserialize_value(value)
            else:
                # Локальный кеш
                if cache_key in self.local_cache:
                    cached_item = self.local_cache[cache_key]
                    if cached_item["expires"] > datetime.now():
                        self.cache_stats["hits"] += 1
                        return cached_item["value"]
                    else:
                        del self.local_cache[cache_key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения из кеша: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Установка значения в кеш"""
        cache_key = self._generate_key(key)
        ttl = ttl or settings.CACHE_TTL
        
        try:
            serialized_value = self._serialize_value(value)
            
            if self.redis_client:
                await self.redis_client.setex(cache_key, ttl, serialized_value)
            else:
                # Локальный кеш
                self.local_cache[cache_key] = {
                    "value": value,
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Ошибка установки в кеш: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кеша"""
        cache_key = self._generate_key(key)
        
        try:
            if self.redis_client:
                await self.redis_client.delete(cache_key)
            else:
                self.local_cache.pop(cache_key, None)
            
            self.cache_stats["deletes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления из кеша: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Очистка кеша по паттерну"""
        try:
            if self.redis_client:
                keys = await self.redis_client.keys(f"{settings.CACHE_KEY_PREFIX}:{pattern}")
                if keys:
                    await self.redis_client.delete(*keys)
                    return len(keys)
            else:
                # Локальный кеш
                keys_to_delete = [
                    key for key in self.local_cache.keys() 
                    if pattern in key
                ]
                for key in keys_to_delete:
                    del self.local_cache[key]
                return len(keys_to_delete)
            
            return 0
            
        except Exception as e:
            logger.error(f"Ошибка очистки кеша по паттерну: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кеша"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "redis_connected": self.redis_client is not None,
            "local_cache_size": len(self.local_cache)
        }


# Глобальный экземпляр менеджера кеша
cache_manager = CacheManager()


def cache_key_from_args(*args, **kwargs) -> str:
    """Генерация ключа кеша из аргументов функции"""
    key_parts = []
    
    for arg in args:
        if hasattr(arg, '__dict__'):
            # Для объектов берем имя класса
            key_parts.append(arg.__class__.__name__)
        else:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Декоратор для кеширования результатов функций"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Генерируем ключ кеша
            cache_key = f"{key_prefix}:{func.__name__}:{cache_key_from_args(*args, **kwargs)}"
            
            # Пытаемся получить из кеша
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Выполняем функцию
            result = await func(*args, **kwargs)
            
            # Сохраняем в кеш
            await cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache set for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


# Специализированные функции кеширования для частых запросов
class QueryCache:
    """Кеш для часто используемых запросов"""
    
    @staticmethod
    async def get_cities() -> Optional[List[Any]]:
        """Получение списка городов из кеша"""
        return await cache_manager.get("cities:all")
    
    @staticmethod
    async def set_cities(cities: List[Any], ttl: int = 3600):
        """Кеширование списка городов"""
        await cache_manager.set("cities:all", cities, ttl)
    
    @staticmethod
    async def get_request_types() -> Optional[List[Any]]:
        """Получение типов заявок из кеша"""
        return await cache_manager.get("request_types:all")
    
    @staticmethod
    async def set_request_types(request_types: List[Any], ttl: int = 3600):
        """Кеширование типов заявок"""
        await cache_manager.set("request_types:all", request_types, ttl)
    
    @staticmethod
    async def get_directions() -> Optional[List[Any]]:
        """Получение направлений из кеша"""
        return await cache_manager.get("directions:all")
    
    @staticmethod
    async def set_directions(directions: List[Any], ttl: int = 3600):
        """Кеширование направлений"""
        await cache_manager.set("directions:all", directions, ttl)
    
    @staticmethod
    async def get_masters_by_city(city_id: int) -> Optional[List[Any]]:
        """Получение мастеров по городу из кеша"""
        return await cache_manager.get(f"masters:city:{city_id}")
    
    @staticmethod
    async def set_masters_by_city(city_id: int, masters: List[Any], ttl: int = 1800):
        """Кеширование мастеров по городу"""
        await cache_manager.set(f"masters:city:{city_id}", masters, ttl)
    
    @staticmethod
    async def invalidate_masters_cache():
        """Инвалидация кеша мастеров"""
        await cache_manager.clear_pattern("masters:*")
    
    @staticmethod
    async def get_user_by_login(login: str) -> Optional[Any]:
        """Получение пользователя по логину из кеша"""
        return await cache_manager.get(f"user:login:{login}")
    
    @staticmethod
    async def set_user_by_login(login: str, user: Any, ttl: int = 900):
        """Кеширование пользователя по логину"""
        await cache_manager.set(f"user:login:{login}", user, ttl)
    
    @staticmethod
    async def invalidate_user_cache(login: str):
        """Инвалидация кеша пользователя"""
        await cache_manager.delete(f"user:login:{login}")


# Инициализация кеша при старте приложения
async def init_cache():
    """Инициализация системы кеширования"""
    await cache_manager.initialize()


# Очистка кеша при завершении приложения
async def cleanup_cache():
    """Очистка системы кеширования"""
    await cache_manager.close() 