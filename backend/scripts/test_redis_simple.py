#!/usr/bin/env python3
"""
Простой тест подключения к Redis (только синхронный)
"""
import redis
import sys

def test_redis_connection():
    """Тест подключения к Redis"""
    try:
        # Подключение к Redis через WSL (localhost:6379)
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Проверка подключения
        response = r.ping()
        print(f"✅ Подключение к Redis: {response}")
        
        # Тест записи и чтения
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print(f"✅ Запись/чтение: {value}")
        
        # Тест с TTL
        r.set('test_ttl', 'value_with_ttl', ex=10)
        ttl = r.ttl('test_ttl')
        print(f"✅ TTL тест: {ttl} секунд")
        
        # Тест списка
        r.lpush('test_list', 'item1', 'item2', 'item3')
        list_items = r.lrange('test_list', 0, -1)
        print(f"✅ Список: {list_items}")
        
        # Очистка
        r.delete('test_key', 'test_ttl', 'test_list')
        print("✅ Очистка выполнена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_redis_info():
    """Получение базовой информации о Redis"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Проверка версии через CONFIG GET
        try:
            config = r.config_get('*')
            print(f"✅ Конфигурация Redis получена")
        except (redis.ResponseError, redis.AuthenticationError) as e:
            print(f"✅ Redis работает (конфигурация недоступна: {e})")
            
        # Проверка количества ключей
        db_size = r.dbsize()
        print(f"✅ Количество ключей в БД: {db_size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🔍 Тестирование подключения к Redis...")
    print("=" * 50)
    
    # Тест подключения
    connection_result = test_redis_connection()
    print()
    
    # Тест информации
    info_result = test_redis_info()
    print()
    
    # Итоговый результат
    if connection_result and info_result:
        print("🎉 Все тесты прошли успешно! Redis готов к использованию.")
        return 0
    else:
        print("❌ Некоторые тесты не прошли. Проверьте настройки Redis.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 