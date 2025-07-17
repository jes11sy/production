#!/usr/bin/env python3
"""
Демонстрационный скрипт для API системы управления заявками
Показывает основные возможности API с примерами использования
"""

import asyncio
import httpx
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ApiDemo:
    """Демонстрация API с примерами"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def print_section(self, title: str):
        """Печать заголовка секции"""
        print(f"\n{'='*60}")
        print(f"🔥 {title}")
        print(f"{'='*60}")
    
    def print_request(self, method: str, url: str, data: Optional[Dict] = None):
        """Печать информации о запросе"""
        print(f"\n📡 {method} {url}")
        if data:
            print(f"📋 Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    def print_response(self, response: httpx.Response):
        """Печать ответа"""
        status_emoji = "✅" if response.status_code < 400 else "❌"
        print(f"{status_emoji} Status: {response.status_code}")
        try:
            response_data = response.json()
            print(f"📄 Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except (ValueError, json.JSONDecodeError) as e:
            print(f"📄 Response (non-JSON): {response.text}")
    
    async def demo_health_check(self):
        """Демонстрация проверки здоровья системы"""
        self.print_section("ПРОВЕРКА ЗДОРОВЬЯ СИСТЕМЫ")
        
        # Базовая проверка
        print("\n🏥 Базовая проверка здоровья")
        url = f"{self.base_url}/health"
        self.print_request("GET", url)
        
        response = await self.client.get(url)
        self.print_response(response)
        
        # Детальная проверка (требует аутентификации)
        if self.auth_token:
            print("\n🔬 Детальная проверка здоровья")
            url = f"{self.base_url}/api/v1/health/detailed"
            self.print_request("GET", url)
            
            response = await self.client.get(
                url,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            self.print_response(response)
    
    async def demo_authentication(self):
        """Демонстрация аутентификации"""
        self.print_section("АУТЕНТИФИКАЦИЯ")
        
        # Примеры учетных данных
        credentials_examples = [
            {
                "name": "Мастер",
                "login": "master001",
                "password": "password123"
            },
            {
                "name": "Сотрудник колл-центра",
                "login": "callcenter_user",
                "password": "employee_pass456"
            },
            {
                "name": "Администратор",
                "login": "admin",
                "password": "admin_secure789"
            }
        ]
        
        for cred in credentials_examples:
            print(f"\n👤 Попытка входа: {cred['name']}")
            url = f"{self.base_url}/api/v1/auth/login"
            data = {
                "login": cred["login"],
                "password": cred["password"]
            }
            
            self.print_request("POST", url, data)
            
            response = await self.client.post(url, json=data)
            self.print_response(response)
            
            if response.status_code == 200:
                response_data = response.json()
                self.auth_token = response_data.get("access_token")
                print(f"🎉 Успешный вход! Токен сохранен.")
                
                # Получение информации о пользователе
                print(f"\n📋 Информация о пользователе")
                me_url = f"{self.base_url}/api/v1/auth/me"
                self.print_request("GET", me_url)
                
                me_response = await self.client.get(
                    me_url,
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                self.print_response(me_response)
                break
            else:
                print(f"❌ Ошибка входа")
    
    async def demo_requests_api(self):
        """Демонстрация API заявок"""
        if not self.auth_token:
            print("⚠️ Требуется аутентификация для демонстрации API заявок")
            return
            
        self.print_section("API ЗАЯВОК")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Получение справочных данных
        print("\n📚 Получение справочных данных")
        
        # Города
        cities_url = f"{self.base_url}/api/v1/requests/cities/"
        self.print_request("GET", cities_url)
        cities_response = await self.client.get(cities_url, headers=headers)
        self.print_response(cities_response)
        
        # Типы заявок
        types_url = f"{self.base_url}/api/v1/requests/request-types/"
        self.print_request("GET", types_url)
        types_response = await self.client.get(types_url, headers=headers)
        self.print_response(types_response)
        
        # Создание заявки
        print("\n📝 Создание новой заявки")
        create_url = f"{self.base_url}/api/v1/requests/"
        
        # Полный пример заявки
        full_request_data = {
            "city_id": 1,
            "request_type_id": 1,
            "client_phone": "+7 (999) 123-45-67",
            "client_name": "Иванов Иван Иванович",
            "address": "г. Москва, ул. Примерная, д. 123, кв. 45",
            "meeting_date": "2025-01-20T14:30:00",
            "direction_id": 1,
            "problem": "Не работает кондиционер, требуется диагностика",
            "status": "new",
            "advertising_campaign_id": 1,
            "ats_number": "ATS-2025-001",
            "call_center_name": "Петрова Анна",
            "call_center_notes": "Клиент очень вежливый, просит перезвонить после 15:00"
        }
        
        self.print_request("POST", create_url, full_request_data)
        create_response = await self.client.post(create_url, json=full_request_data, headers=headers)
        self.print_response(create_response)
        
        request_id = None
        if create_response.status_code == 200:
            request_id = create_response.json().get("id")
            print(f"✅ Заявка создана с ID: {request_id}")
        
        # Минимальный пример заявки
        print("\n📝 Создание минимальной заявки")
        minimal_request_data = {
            "city_id": 1,
            "request_type_id": 2,
            "client_phone": "+7 (999) 987-65-43",
            "client_name": "Петров Петр"
        }
        
        self.print_request("POST", create_url, minimal_request_data)
        minimal_response = await self.client.post(create_url, json=minimal_request_data, headers=headers)
        self.print_response(minimal_response)
        
        # Получение списка заявок
        print("\n📋 Получение списка заявок")
        list_url = f"{self.base_url}/api/v1/requests/?skip=0&limit=10"
        self.print_request("GET", list_url)
        list_response = await self.client.get(list_url, headers=headers)
        self.print_response(list_response)
        
        # Получение конкретной заявки
        if request_id:
            print(f"\n🔍 Получение заявки #{request_id}")
            get_url = f"{self.base_url}/api/v1/requests/{request_id}"
            self.print_request("GET", get_url)
            get_response = await self.client.get(get_url, headers=headers)
            self.print_response(get_response)
            
            # Обновление заявки
            print(f"\n✏️ Обновление заявки #{request_id}")
            update_url = f"{self.base_url}/api/v1/requests/{request_id}"
            update_data = {
                "status": "in_progress",
                "master_notes": "Начата диагностика кондиционера",
                "master_id": 1
            }
            
            self.print_request("PUT", update_url, update_data)
            update_response = await self.client.put(update_url, json=update_data, headers=headers)
            self.print_response(update_response)
    
    async def demo_transactions_api(self):
        """Демонстрация API транзакций"""
        if not self.auth_token:
            print("⚠️ Требуется аутентификация для демонстрации API транзакций")
            return
            
        self.print_section("API ТРАНЗАКЦИЙ")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Создание транзакции
        print("\n💰 Создание транзакции (расход)")
        create_url = f"{self.base_url}/api/v1/transactions/"
        
        expense_data = {
            "city_id": 1,
            "transaction_type_id": 1,
            "amount": 15000.50,
            "notes": "Закупка запчастей для ремонта кондиционеров",
            "specified_date": "2025-01-15",
            "payment_reason": "Материалы для заявки #123"
        }
        
        self.print_request("POST", create_url, expense_data)
        create_response = await self.client.post(create_url, json=expense_data, headers=headers)
        self.print_response(create_response)
        
        # Создание зарплатной транзакции
        print("\n💼 Создание транзакции (зарплата)")
        salary_data = {
            "city_id": 1,
            "transaction_type_id": 2,
            "amount": 5000.00,
            "notes": "Оплата услуг мастера",
            "specified_date": "2025-01-15",
            "payment_reason": "Заработная плата"
        }
        
        self.print_request("POST", create_url, salary_data)
        salary_response = await self.client.post(create_url, json=salary_data, headers=headers)
        self.print_response(salary_response)
        
        # Получение списка транзакций
        print("\n📋 Получение списка транзакций")
        list_url = f"{self.base_url}/api/v1/transactions/?skip=0&limit=10"
        self.print_request("GET", list_url)
        list_response = await self.client.get(list_url, headers=headers)
        self.print_response(list_response)
    
    async def demo_users_api(self):
        """Демонстрация API пользователей"""
        if not self.auth_token:
            print("⚠️ Требуется аутентификация для демонстрации API пользователей")
            return
            
        self.print_section("API ПОЛЬЗОВАТЕЛЕЙ")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Получение списка мастеров
        print("\n👨‍🔧 Получение списка мастеров")
        masters_url = f"{self.base_url}/api/v1/users/masters/"
        self.print_request("GET", masters_url)
        masters_response = await self.client.get(masters_url, headers=headers)
        self.print_response(masters_response)
        
        # Создание нового мастера (может потребовать права менеджера)
        print("\n➕ Создание нового мастера")
        create_master_url = f"{self.base_url}/api/v1/users/masters/"
        master_data = {
            "city_id": 1,
            "full_name": "Сидоров Алексей Владимирович",
            "phone_number": "+7 (999) 555-12-34",
            "birth_date": "1985-03-15",
            "passport": "4510 123456",
            "login": f"master_demo_{datetime.now().strftime('%H%M%S')}",
            "password": "secure_pass123",
            "chat_id": "telegram_123456789",
            "notes": "Специализация: кондиционеры, стаж 8 лет"
        }
        
        self.print_request("POST", create_master_url, master_data)
        create_master_response = await self.client.post(create_master_url, json=master_data, headers=headers)
        self.print_response(create_master_response)
        
        # Получение списка сотрудников
        print("\n👥 Получение списка сотрудников")
        employees_url = f"{self.base_url}/api/v1/users/employees/"
        self.print_request("GET", employees_url)
        employees_response = await self.client.get(employees_url, headers=headers)
        self.print_response(employees_response)
    
    async def demo_database_api(self):
        """Демонстрация API базы данных"""
        if not self.auth_token:
            print("⚠️ Требуется аутентификация для демонстрации API базы данных")
            return
            
        self.print_section("API БАЗЫ ДАННЫХ")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Статистика базы данных
        print("\n📊 Статистика базы данных")
        stats_url = f"{self.base_url}/api/v1/database/statistics"
        self.print_request("GET", stats_url)
        stats_response = await self.client.get(stats_url, headers=headers)
        self.print_response(stats_response)
        
        # Отчет по оптимизации
        print("\n🔧 Отчет по оптимизации")
        report_url = f"{self.base_url}/api/v1/database/optimization-report"
        self.print_request("GET", report_url)
        report_response = await self.client.get(report_url, headers=headers)
        self.print_response(report_response)
    
    async def demo_error_handling(self):
        """Демонстрация обработки ошибок"""
        self.print_section("ОБРАБОТКА ОШИБОК")
        
        # Неавторизованный запрос
        print("\n🚫 Неавторизованный запрос")
        url = f"{self.base_url}/api/v1/requests/"
        self.print_request("GET", url)
        response = await self.client.get(url)
        self.print_response(response)
        
        # Неверные учетные данные
        print("\n🔐 Неверные учетные данные")
        auth_url = f"{self.base_url}/api/v1/auth/login"
        wrong_data = {
            "login": "wrong_user",
            "password": "wrong_password"
        }
        self.print_request("POST", auth_url, wrong_data)
        wrong_response = await self.client.post(auth_url, json=wrong_data)
        self.print_response(wrong_response)
        
        # Валидационная ошибка
        print("\n❌ Ошибка валидации")
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            create_url = f"{self.base_url}/api/v1/requests/"
            invalid_data = {
                "client_phone": "очень_длинный_номер_телефона_который_превышает_максимальную_длину",
                "client_name": "Тест"
                # Отсутствует обязательное поле city_id
            }
            self.print_request("POST", create_url, invalid_data)
            invalid_response = await self.client.post(create_url, json=invalid_data, headers=headers)
            self.print_response(invalid_response)
        
        # Несуществующий ресурс
        print("\n🔍 Несуществующий ресурс")
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            notfound_url = f"{self.base_url}/api/v1/requests/99999"
            self.print_request("GET", notfound_url)
            notfound_response = await self.client.get(notfound_url, headers=headers)
            self.print_response(notfound_response)
    
    async def run_full_demo(self):
        """Запуск полной демонстрации"""
        print("🚀 ДЕМОНСТРАЦИЯ API СИСТЕМЫ УПРАВЛЕНИЯ ЗАЯВКАМИ")
        print(f"🌐 Базовый URL: {self.base_url}")
        print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Проверка здоровья
            await self.demo_health_check()
            
            # Аутентификация
            await self.demo_authentication()
            
            # API заявок
            await self.demo_requests_api()
            
            # API транзакций
            await self.demo_transactions_api()
            
            # API пользователей
            await self.demo_users_api()
            
            # API базы данных
            await self.demo_database_api()
            
            # Обработка ошибок
            await self.demo_error_handling()
            
            self.print_section("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
            print("✅ Все примеры успешно выполнены!")
            print("📖 Для получения полной документации откройте:")
            print(f"   🔗 Swagger UI: {self.base_url}/docs")
            print(f"   🔗 ReDoc: {self.base_url}/redoc")
            print(f"   🔗 OpenAPI Schema: {self.base_url}/openapi.json")
            
        except Exception as e:
            print(f"\n❌ Ошибка во время демонстрации: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Демонстрация API системы управления заявками")
    parser.add_argument("--url", default="http://localhost:8000", help="Базовый URL API")
    parser.add_argument("--section", choices=[
        "health", "auth", "requests", "transactions", "users", "database", "errors", "all"
    ], default="all", help="Какую секцию демонстрировать")
    
    args = parser.parse_args()
    
    async with ApiDemo(args.url) as demo:
        if args.section == "all":
            await demo.run_full_demo()
        elif args.section == "health":
            await demo.demo_health_check()
        elif args.section == "auth":
            await demo.demo_authentication()
        elif args.section == "requests":
            await demo.demo_authentication()
            await demo.demo_requests_api()
        elif args.section == "transactions":
            await demo.demo_authentication()
            await demo.demo_transactions_api()
        elif args.section == "users":
            await demo.demo_authentication()
            await demo.demo_users_api()
        elif args.section == "database":
            await demo.demo_authentication()
            await demo.demo_database_api()
        elif args.section == "errors":
            await demo.demo_authentication()
            await demo.demo_error_handling()


if __name__ == "__main__":
    asyncio.run(main()) 