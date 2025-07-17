#!/usr/bin/env python3
"""
Скрипт для тестирования всех сервисов Docker Compose
"""
import requests
import time
import sys

def test_service(name, url, expected_status=200):
    """Тестирует доступность сервиса"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ {name}: OK (status {response.status_code})")
            return True
        else:
            print(f"❌ {name}: ERROR (status {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: ERROR ({e})")
        return False

def main():
    """Основная функция тестирования"""
    print("🔍 Тестирование сервисов Docker Compose...")
    print("=" * 50)
    
    services = [
        ("Grafana", "http://localhost:3000"),
        ("Prometheus", "http://localhost:9090"),
        ("Backend API", "http://localhost:8000"),
        ("Backend Health", "http://localhost:8000/health"),
        ("Backend Docs", "http://localhost:8000/docs"),
    ]
    
    results = []
    
    for name, url in services:
        result = test_service(name, url)
        results.append(result)
        time.sleep(1)  # Небольшая пауза между запросами
    
    print("=" * 50)
    print(f"📊 Результаты: {sum(results)}/{len(results)} сервисов работают")
    
    if all(results):
        print("🎉 Все сервисы работают корректно!")
        sys.exit(0)
    else:
        print("⚠️  Некоторые сервисы недоступны")
        sys.exit(1)

if __name__ == "__main__":
    main() 