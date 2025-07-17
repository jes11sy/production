# 🧪 ПРОДВИНУТОЕ ТЕСТИРОВАНИЕ

Этот документ описывает новые типы тестов, которые были добавлены в систему для комплексной проверки готовности к production.

## 📋 ТИПЫ ТЕСТОВ

### 1. 🎯 E2E ТЕСТЫ (End-to-End)
**Файл:** `tests/test_e2e_scenarios.py`

Полное тестирование пользовательских сценариев от начала до конца:
- Полный жизненный цикл заявки
- Управление пользователями
- Отчетность и аналитика
- Интеграция с внешними системами
- Сценарии безопасности
- Производительность в реальных условиях
- Консистентность данных
- Мониторинг и здоровье системы

### 2. ⚡ LOAD TESTING (Нагрузочное тестирование)
**Файл:** `tests/test_load_testing.py`

Тестирование производительности под нагрузкой:
- Базовые нагрузочные тесты
- Стресс-тесты с высокой нагрузкой
- Тесты пиковой нагрузки (spike testing)
- Тесты на выносливость
- Тестирование конкретных endpoints
- Тесты утечек памяти
- Лимиты одновременных соединений
- Реалистичные пользовательские сценарии

### 3. 🔥 CHAOS ENGINEERING (Тестирование отказоустойчивости)
**Файл:** `tests/test_chaos_engineering.py`

Проверка поведения системы при сбоях:
- Сбои базы данных
- Сетевые проблемы
- Нехватка ресурсов
- Сбои внешних сервисов
- Тесты восстановления
- Graceful degradation

### 4. 📋 CONTRACT TESTING (Тестирование API контрактов)
**Файл:** `tests/test_contract_testing.py`

Проверка соответствия API контрактам:
- Валидация схем запросов и ответов
- Обратная совместимость
- Эволюция контрактов
- Соответствие документации

## 🚀 ЗАПУСК ТЕСТОВ

### Автоматический запуск всех тестов
```bash
# Запуск всех типов тестов
python run_advanced_tests.py

# Запуск конкретных типов тестов
python run_advanced_tests.py --types e2e load

# Быстрый тест
python run_advanced_tests.py --quick
```

### Ручной запуск отдельных типов

#### E2E тесты
```bash
pytest tests/test_e2e_scenarios.py -v --asyncio-mode=auto
```

#### Load тесты
```bash
pytest tests/test_load_testing.py -v --asyncio-mode=auto -s
```

#### Chaos Engineering тесты
```bash
pytest tests/test_chaos_engineering.py -v --asyncio-mode=auto -s
```

#### Contract тесты
```bash
pytest tests/test_contract_testing.py -v --asyncio-mode=auto
```

## 📊 ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ

### Успешные результаты
- **E2E тесты:** Все пользовательские сценарии работают корректно
- **Load тесты:** Система выдерживает заданную нагрузку
- **Chaos тесты:** Система показывает отказоустойчивость
- **Contract тесты:** API соответствует контрактам

### Критерии оценки

#### E2E тесты
- ✅ **Отлично:** Все тесты проходят
- ⚠️ **Хорошо:** 80%+ тестов проходят
- ❌ **Плохо:** Менее 80% тестов проходят

#### Load тесты
- ✅ **Отлично:** Error rate < 5%, Response time < 2s
- ⚠️ **Хорошо:** Error rate < 10%, Response time < 5s
- ❌ **Плохо:** Error rate > 10% или Response time > 5s

#### Chaos тесты
- ✅ **Отлично:** Success rate > 50% во время хаоса
- ⚠️ **Хорошо:** Success rate > 20% во время хаоса
- ❌ **Плохо:** Success rate < 20% во время хаоса

#### Contract тесты
- ✅ **Отлично:** 100% endpoints соответствуют контрактам
- ⚠️ **Хорошо:** 80%+ endpoints соответствуют контрактам
- ❌ **Плохо:** Менее 80% endpoints соответствуют контрактам

## 🔧 КОНФИГУРАЦИЯ

### Настройки нагрузочного тестирования
```python
class LoadTestConfig:
    CONCURRENT_USERS = 50      # Количество одновременных пользователей
    REQUESTS_PER_USER = 20     # Запросов на пользователя
    RAMP_UP_TIME = 10          # Время разгона (секунды)
    TEST_DURATION = 60         # Длительность теста (секунды)
    ACCEPTABLE_RESPONSE_TIME = 2.0  # Допустимое время ответа
    ACCEPTABLE_ERROR_RATE = 0.05    # Допустимый процент ошибок
```

### Настройки Chaos Engineering
```python
# Типы сценариев хаоса
- Database failures
- Network issues  
- Resource exhaustion
- Service failures
```

## 📈 ОТЧЕТЫ

### Автоматические отчеты
Скрипт `run_advanced_tests.py` автоматически генерирует:
- **Текстовый отчет:** `advanced_test_report_YYYYMMDD_HHMMSS.txt`
- **JSON данные:** `advanced_test_report_YYYYMMDD_HHMMSS.json`

### Структура отчета
```
📊 ОТЧЕТ О ПРОДВИНУТОМ ТЕСТИРОВАНИИ
🕐 Время начала: 2025-01-15T10:00:00
🕐 Время окончания: 2025-01-15T10:30:00
⏱️ Общая продолжительность: 1800.00 секунд

📋 РЕЗУЛЬТАТЫ ПО ТИПАМ ТЕСТОВ:
E2E          | ✅ ПРОШЕЛ    |   600.00s
LOAD         | ✅ ПРОШЕЛ    |   900.00s
CHAOS        | ⚠️ ЧАСТИЧНО  |   800.00s
CONTRACT     | ✅ ПРОШЕЛ    |   400.00s

ИТОГО: 3/4 тестов прошли успешно
```

## 🛠️ ТРЕБОВАНИЯ

### Системные требования
- Python 3.11+
- PostgreSQL (запущен)
- Redis (запущен)
- Достаточно свободной памяти (рекомендуется 4GB+)

### Зависимости
```bash
pip install -r requirements.txt

# Дополнительные зависимости для тестирования
pip install pytest-asyncio httpx aiohttp psutil jsonschema
```

### Переменные окружения
```bash
# Убедитесь, что настроены все необходимые переменные
cp env.example .env
# Отредактируйте .env файл
```

## 🚨 TROUBLESHOOTING

### Частые проблемы

#### 1. Тесты не запускаются
```bash
# Проверьте зависимости
pip install -r requirements.txt

# Проверьте переменные окружения
python -c "from app.core.config import settings; print('Config OK')"
```

#### 2. Load тесты падают
```bash
# Увеличьте лимиты системы
ulimit -n 4096

# Проверьте доступность портов
netstat -an | grep 8000
```

#### 3. Chaos тесты не работают
```bash
# Убедитесь, что система запущена
python run.py &

# Проверьте доступность endpoints
curl http://localhost:8000/api/v1/health
```

#### 4. Contract тесты не проходят
```bash
# Проверьте схемы API
python -c "from app.core.schemas import *; print('Schemas OK')"

# Проверьте endpoints
curl http://localhost:8000/docs
```

## 🎯 РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ

### Перед релизом
1. Запустите все типы тестов: `python run_advanced_tests.py`
2. Убедитесь, что success rate > 80%
3. Проанализируйте отчеты на предмет критических проблем
4. Исправьте найденные проблемы

### В процессе разработки
1. Запускайте E2E тесты после крупных изменений
2. Используйте Load тесты для проверки производительности
3. Применяйте Chaos тесты для проверки отказоустойчивости
4. Проверяйте Contract тесты при изменении API

### Мониторинг в production
1. Настройте регулярный запуск E2E тестов
2. Используйте метрики из Load тестов для capacity planning
3. Применяйте принципы Chaos Engineering в production
4. Мониторьте соответствие API контрактам

## 📚 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ

### Полезные ссылки
- [Pytest Documentation](https://docs.pytest.org/)
- [Chaos Engineering Principles](https://principlesofchaos.org/)
- [Contract Testing Guide](https://pact.io/)
- [Load Testing Best Practices](https://k6.io/docs/)

### Интеграция с CI/CD
```yaml
# Пример для GitHub Actions
- name: Run Advanced Tests
  run: |
    python run_advanced_tests.py --types e2e contract
    
- name: Run Load Tests (nightly)
  run: |
    python run_advanced_tests.py --types load
  if: github.event_name == 'schedule'
```

---

**Создано:** 15 января 2025  
**Версия:** 1.0.0  
**Статус:** Готово к использованию 