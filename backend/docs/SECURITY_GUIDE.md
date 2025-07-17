# 🔒 Руководство по безопасности

## Обзор

Этот документ содержит рекомендации по обеспечению безопасности приложения и инструкции по правильному использованию системы безопасности.

## 🔑 Настройка SECRET_KEY

### Критические требования (ИСПРАВЛЕНО)

⚠️ **ВАЖНО**: SECRET_KEY теперь имеет строгие требования безопасности:

1. **Минимальная длина**: 32 символа (для development)
2. **Рекомендуемая длина**: 64+ символов (для production)
3. **Обязательность**: Приложение не запустится без SECRET_KEY
4. **Энтропия**: Ключ должен быть криптографически стойким

### Генерация SECRET_KEY

```bash
# Для development (32 символа)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Для production (64+ символов, рекомендуется)
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Настройка окружения

1. Скопируйте `env.example` в `.env`:
   ```bash
   cp env.example .env
   ```

2. Отредактируйте `.env` файл и установите реальные значения:
   ```env
   SECRET_KEY=your-64-character-cryptographically-strong-secret-key-here
   ENVIRONMENT=development
   ```

3. **НИКОГДА** не коммитьте `.env` файл в git!

### Автоматическая проверка конфигурации

Приложение автоматически проверяет:
- ✅ Наличие SECRET_KEY в переменных окружения
- ✅ Минимальную длину ключа (32 символа)
- ✅ Дополнительные требования для production (64+ символов)
- ✅ Что SECRET_KEY не является примером из документации

## 🔐 HTTPS Поддержка (НОВОЕ)

### Development HTTPS

Для запуска с HTTPS в development:

```bash
# Автоматическое создание SSL сертификатов и запуск
python run_https.py
```

Приложение автоматически:
- Создает самоподписанные SSL сертификаты в папке `ssl/`
- Настраивает современные параметры SSL/TLS
- Запускается на порту 8443 с HTTPS

### Production HTTPS

Для production используйте реальные SSL сертификаты:

```bash
# Настройте пути к сертификатам в .env
SSL_CERT_PATH=/path/to/your/cert.pem
SSL_KEY_PATH=/path/to/your/key.pem

# Запуск с SSL
uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

## 📁 Система безопасного доступа к файлам (НОВОЕ)

### Контроль доступа по ролям

Система теперь включает строгий контроль доступа:

```python
# Роли и их права доступа к файлам:
- admin: Полный доступ ко всем файлам
- director: Полный доступ ко всем файлам  
- manager: Доступ к файлам своих заявок
- avitolog: Доступ к файлам своих заявок
- master: Доступ только к файлам своих заявок
```

### Безопасные API эндпоинты

```python
# Безопасная загрузка файлов
GET /api/v1/secure-files/download/{file_path:path}

# Безопасный просмотр файлов
GET /api/v1/secure-files/view/{file_path:path}
```

### Защита от атак

1. **Path Traversal Protection**: Проверка на `../` и другие попытки выхода из разрешенной директории
2. **MIME Type Validation**: Проверка типов файлов
3. **Role-based Access**: Контроль доступа по ролям пользователей
4. **Secure Headers**: Безопасные HTTP заголовки

### Использование API безопасного доступа

```javascript
// Frontend - безопасная загрузка файла
const downloadFile = async (filePath) => {
  const response = await fetch(`/api/v1/secure-files/download/${filePath}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    const blob = await response.blob();
    // Обработка файла
  }
};
```

## 🛡️ Замена отладочных уведомлений (ИСПРАВЛЕНО)

### Проблема
Ранее использовались небезопасные `alert()` и `console.log()` для отладки.

### Решение
Внедрена система типизированных уведомлений:

```typescript
// Новая система уведомлений
import { useNotification } from '../contexts/NotificationContext';

const { showNotification } = useNotification();

// Вместо alert()
showNotification('Транзакция создана успешно', 'success');
showNotification('Ошибка при создании', 'error');
showNotification('Проверьте данные', 'warning');
showNotification('Информация сохранена', 'info');
```

### Типы уведомлений
- `success` - Успешные операции (зеленый)
- `error` - Ошибки (красный)
- `warning` - Предупреждения (желтый)
- `info` - Информационные сообщения (синий)

## 🔧 Настройка Redis кеширования (НОВОЕ)

### Конфигурация Redis

```env
REDIS_URL=redis://localhost:6379
REDIS_TTL_METRICS=300  # 5 минут для метрик
REDIS_TTL_CACHE=600    # 10 минут для общего кеша
```

### Безопасность Redis

1. **Аутентификация**: Настройте пароль для Redis в production
2. **Сетевая безопасность**: Ограничьте доступ к Redis только с backend серверов
3. **Шифрование**: Используйте TLS для соединений с Redis в production

```bash
# Пример конфигурации Redis с аутентификацией
redis-server --requirepass your-strong-password
```

## 🚨 Чек-лист безопасности (ОБНОВЛЕН)

### Критические исправления (✅ ВЫПОЛНЕНО)
- [x] ✅ **SECRET_KEY**: Строгие требования к длине и энтропии
- [x] ✅ **Файловая безопасность**: Контроль доступа по ролям
- [x] ✅ **HTTPS**: Поддержка SSL/TLS для development и production
- [x] ✅ **Уведомления**: Замена alert() на безопасные уведомления
- [x] ✅ **Redis**: Кеширование с TTL и безопасными настройками

### Дополнительные рекомендации
- [ ] ❌ **Rate Limiting**: Ограничение частоты запросов
- [ ] ❌ **WAF**: Web Application Firewall
- [ ] ❌ **Monitoring**: Мониторинг безопасности в реальном времени
- [ ] ❌ **Backup**: Регулярные зашифрованные бэкапы

## 📊 Мониторинг безопасности

### Логирование безопасности

```python
# Логирование попыток доступа к файлам
logger.info(f"File access attempt: user={user.id}, file={file_path}, result={result}")

# Логирование неудачных аутентификаций
logger.warning(f"Authentication failed: {username}")
```

### Метрики безопасности

- Количество неудачных попыток входа
- Попытки несанкционированного доступа к файлам
- Использование Redis кеша (hit/miss ratio)
- SSL/TLS соединения

## 🔍 Аудит безопасности

### Автоматические проверки

```bash
# Проверка конфигурации безопасности
python -c "from app.core.config import settings; print('Security OK' if settings.SECRET_KEY and len(settings.SECRET_KEY) >= 32 else 'Security FAIL')"

# Проверка SSL сертификатов
openssl x509 -in ssl/cert.pem -text -noout

# Проверка Redis подключения
redis-cli ping
```

### Регулярные проверки

1. **Еженедельно**: Проверка логов на подозрительную активность
2. **Ежемесячно**: Обновление зависимостей и проверка уязвимостей
3. **Ежеквартально**: Полный аудит безопасности

## 🛠️ Устранение уязвимостей

### Обновление зависимостей

```bash
# Проверка уязвимостей
pip audit

# Обновление зависимостей
pip install --upgrade -r requirements.txt
```

### Мониторинг уязвимостей

```bash
# Установка инструментов безопасности
pip install safety bandit

# Проверка безопасности кода
bandit -r app/

# Проверка уязвимостей зависимостей
safety check
```

## 📞 Экстренное реагирование

### При обнаружении уязвимости

1. **Немедленно**: Изолируйте скомпрометированную систему
2. **Оцените**: Масштаб потенциального ущерба
3. **Исправьте**: Примените патч безопасности
4. **Уведомите**: Информируйте заинтересованные стороны
5. **Документируйте**: Зафиксируйте инцидент и меры по устранению

### Контакты для экстренных случаев

- Системный администратор: [контакт]
- Ответственный за безопасность: [контакт]
- Руководитель проекта: [контакт]

## 📚 Дополнительные ресурсы

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Redis Security](https://redis.io/topics/security)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html) 