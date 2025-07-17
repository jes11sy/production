# 🏗️ Архитектура проекта

## 📋 Обзор системы

**Название:** Система управления заявками  
**Архитектурный паттерн:** Разделение на Frontend и Backend (SPA + REST API)  
**Тип развертывания:** Монолитный, с возможностью декомпозиции  

### Высокоуровневая архитектура

```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────┐
│   React SPA     │ ────────────────► │   FastAPI       │
│   (Frontend)    │                  │   (Backend)     │
└─────────────────┘                  └─────────────────┘
                                              │
                                              │ SQL
                                              ▼
                                     ┌─────────────────┐
                                     │   PostgreSQL    │
                                     │   (Database)    │
                                     └─────────────────┘
```

---

## 🎯 Компоненты системы

### 1. Frontend (React SPA)

#### Технологический стек
- **Framework:** React 19.1.0
- **Language:** TypeScript 5.8.3
- **Build Tool:** Vite 7.0.4
- **UI Library:** HeroUI 2.7.11
- **Styling:** Tailwind CSS 3.4.17
- **Routing:** React Router DOM 7.6.3
- **Forms:** React Hook Form 7.60.0 + Zod 4.0.5
- **State Management:** Zustand 5.0.6
- **Data Fetching:** Tanstack Query 5.83.0
- **HTTP Client:** Axios 1.10.0

#### Структура директорий
```
frontend/
├── src/
│   ├── pages/           # Страницы приложения
│   ├── components/      # Переиспользуемые компоненты
│   ├── api/            # API слой
│   ├── contexts/       # React контексты
│   ├── types/          # TypeScript типы
│   ├── services/       # Сервисы
│   ├── stores/         # Zustand сторы
│   └── assets/         # Статические файлы
├── public/             # Публичные файлы
└── dist/               # Сборка проекта
```

#### Слои архитектуры
1. **Presentation Layer** - React компоненты и страницы
2. **State Management** - Zustand + React Context
3. **Data Layer** - API вызовы и кеширование
4. **Business Logic** - Валидация форм и обработка данных

### 2. Backend (FastAPI)

#### Технологический стек
- **Framework:** FastAPI 0.95.2
- **Language:** Python 3.11
- **ASGI Server:** Uvicorn 0.22.0
- **ORM:** SQLAlchemy 2.0.15 (async)
- **Database:** PostgreSQL 13+
- **Migrations:** Alembic 1.11.1
- **Validation:** Pydantic 1.10.8
- **Authentication:** JWT + httpOnly cookies
- **Password Hashing:** bcrypt 4.3.0

#### Структура директорий
```
backend/
├── app/
│   ├── api/            # API endpoints
│   ├── models/         # SQLAlchemy модели
│   ├── schemas/        # Pydantic схемы
│   ├── crud/           # CRUD операции
│   ├── auth.py         # Аутентификация
│   ├── config.py       # Конфигурация
│   ├── database.py     # Подключение к БД
│   └── main.py         # Главный файл приложения
├── alembic/            # Миграции базы данных
├── media/              # Загруженные файлы
└── venv/               # Виртуальное окружение
```

#### Слои архитектуры
1. **API Layer** - FastAPI endpoints
2. **Business Logic** - Pydantic валидация и обработка
3. **Data Access** - SQLAlchemy ORM
4. **Database** - PostgreSQL

### 3. Database (PostgreSQL)

#### Основные таблицы
- **users** - Пользователи системы
- **masters** - Мастера
- **employees** - Сотрудники
- **administrators** - Администраторы
- **cities** - Города
- **roles** - Роли пользователей
- **requests** - Заявки
- **transactions** - Транзакции
- **advertising_campaigns** - Рекламные кампании
- **request_types** - Типы заявок
- **directions** - Направления работ
- **transaction_types** - Типы транзакций
- **files** - Файлы

### 👥 Роли и права доступа

Система поддерживает многоуровневую систему ролей:

| Роль | Описание | Доступные функции |
|------|----------|-------------------|
| **admin** | Системный администратор | Полный доступ ко всем функциям |
| **director** | Директор | Заявки, мастера, транзакции |
| **manager** | Менеджер | Управление заявками и пользователями |
| **avitolog** | Авитолог | Работа с заявками |
| **callcentr** | Колл-центр | Заявки, входящие заявки, отчет КЦ |
| **master** | Мастер | Свои заявки и транзакции |

**Реализация безопасности:**
- JWT токены в httpOnly cookies
- Проверка прав на уровне API эндпоинтов
- Декораторы для проверки ролей (`require_admin`, `require_manager`, etc.)
- Фильтрация данных по правам доступа

---

## 🔄 Потоки данных

### 1. Аутентификация пользователя

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    
    U->>F: Вход в систему
    F->>B: POST /auth/login
    B->>DB: Проверка credentials
    DB-->>B: User data
    B->>B: Генерация JWT
    B-->>F: httpOnly cookie + user data
    F->>F: Сохранение в AuthContext
    F-->>U: Перенаправление на dashboard
```

### 2. Создание заявки

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    
    U->>F: Заполнение формы
    F->>F: Валидация (Zod)
    F->>B: POST /requests/
    B->>B: Валидация (Pydantic)
    B->>DB: INSERT запись
    DB-->>B: Новая заявка
    B-->>F: Созданная заявка
    F->>F: Обновление UI
    F-->>U: Уведомление об успехе
```

### 3. Загрузка файлов

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant FS as File System
    
    U->>F: Выбор файла
    F->>B: POST /upload-* (multipart)
    B->>B: Валидация файла
    B->>FS: Сохранение файла
    FS-->>B: Путь к файлу
    B-->>F: Информация о файле
    F-->>U: Подтверждение загрузки
```

---

## 🔐 Безопасность

### 1. Аутентификация
- **JWT токены** в httpOnly cookies
- **Автоматическая валидация** токенов middleware
- **Refresh token** ротация
- **Защита от CSRF** через SameSite cookies

### 2. Авторизация
- **Ролевая модель** (admin, director, manager, avitolog, master)
- **Проверка прав доступа** на уровне API
- **Фильтрация данных** по городам для директоров

### 3. Валидация данных
- **Frontend:** Zod схемы для форм
- **Backend:** Pydantic схемы для API
- **Database:** Constraints и типы данных

### 4. Защита файлов
- **Валидация типов файлов** по MIME и расширению
- **Ограничение размера** файлов
- **Безопасные имена файлов** (UUID)

---

## 📊 Паттерны и подходы

### 1. Frontend паттерны

#### Compound Components
```typescript
// Пример HeroUI компонента
<Table>
  <TableHeader>
    <TableColumn>Имя</TableColumn>
    <TableColumn>Статус</TableColumn>
  </TableHeader>
  <TableBody>
    {users.map(user => (
      <TableRow key={user.id}>
        <TableCell>{user.name}</TableCell>
        <TableCell>{user.status}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

#### Custom Hooks
```typescript
// Пример кастомного хука
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

#### Form Handling
```typescript
// React Hook Form + Zod
const schema = z.object({
  name: z.string().min(1, 'Имя обязательно'),
  email: z.string().email('Неверный email'),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema)
});
```

### 2. Backend паттерны

#### Repository Pattern
```python
# CRUD операции
class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

#### Dependency Injection
```python
# FastAPI зависимости
async def get_current_user(
    token: str = Depends(get_token_from_cookie)
) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    return await get_user_by_id(user_id)
```

#### Pydantic Schemas
```python
# Валидация данных
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Пароль должен содержать буквы')
        return v
```

---

## 🚀 Масштабирование и производительность

### 1. Frontend оптимизации

#### Code Splitting
```typescript
// Ленивая загрузка страниц
const LazyDashboard = React.lazy(() => import('./pages/Dashboard'));
const LazyUsers = React.lazy(() => import('./pages/UsersPage'));

// В роутинге
<Route path="/dashboard" element={
  <Suspense fallback={<LoadingSpinner />}>
    <LazyDashboard />
  </Suspense>
} />
```

#### Мемоизация
```typescript
// Оптимизация рендеринга
const UserRow = React.memo(({ user, onEdit, onDelete }) => {
  const handleEdit = useCallback(() => onEdit(user.id), [user.id, onEdit]);
  const handleDelete = useCallback(() => onDelete(user.id), [user.id, onDelete]);
  
  return (
    <tr>
      <td>{user.name}</td>
      <td>
        <button onClick={handleEdit}>Edit</button>
        <button onClick={handleDelete}>Delete</button>
      </td>
    </tr>
  );
});
```

#### Виртуализация
```typescript
// Для больших списков
import { FixedSizeList as List } from 'react-window';

const VirtualizedList = ({ items }) => (
  <List
    height={400}
    itemCount={items.length}
    itemSize={50}
  >
    {({ index, style }) => (
      <div style={style}>
        {items[index].name}
      </div>
    )}
  </List>
);
```

### 2. Backend оптимизации

#### Async/Await
```python
# Асинхронная обработка
async def get_users_with_stats(db: AsyncSession):
    users = await db.execute(select(User))
    stats = await db.execute(select(UserStats))
    return combine_data(users, stats)
```

#### Connection Pooling
```python
# Конфигурация пула соединений
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

#### Кеширование
```python
# Пример кеширования
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cities():
    return db.query(City).all()
```

### 3. Database оптимизации

#### Индексы
```sql
-- Индексы для частых запросов
CREATE INDEX idx_requests_city_id ON requests(city_id);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_created_at ON requests(created_at);
CREATE INDEX idx_transactions_city_date ON transactions(city_id, specified_date);
```

#### Оптимизация запросов
```python
# Eager loading для избежания N+1
query = select(Request).options(
    joinedload(Request.city),
    joinedload(Request.master),
    joinedload(Request.request_type)
)
```

---

## 🔧 Конфигурация и окружения

### 1. Environment Variables

#### Backend (.env)
```bash
# База данных
DATABASE_URL=postgresql://user:password@localhost/db_name
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=user
POSTGRESQL_PASSWORD=password
POSTGRESQL_DATABASE=db_name

# Безопасность
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Файлы
MEDIA_ROOT=media/
MAX_FILE_SIZE=10485760

# Окружение
ENVIRONMENT=development
DEBUG=true
```

#### Frontend (.env)
```bash
# Development
VITE_API_URL=http://localhost:8000/api/v1

# Production
VITE_API_URL=https://api.yourcompany.com/v1
```

### 2. Конфигурационные файлы

#### Vite (vite.config.ts)
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@heroui/react'],
        },
      },
    },
  },
});
```

#### Tailwind (tailwind.config.cjs)
```javascript
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#0070f3',
        secondary: '#7c3aed',
      },
    },
  },
  plugins: [],
};
```

---

## 📋 Качество кода

### 1. TypeScript конфигурация

#### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### 2. ESLint конфигурация

#### eslint.config.js
```javascript
export default tseslint.config([
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs['recommended-latest'],
    ],
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
]);
```

### 3. Линтинг Python

#### .flake8
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    alembic
```

---

## 🔍 Мониторинг и логирование

### 1. Frontend мониторинг

#### Error Boundaries
```typescript
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Отправка в сервис мониторинга
  }

  render() {
    if (this.state.hasError) {
      return <h1>Что-то пошло не так.</h1>;
    }
    return this.props.children;
  }
}
```

### 2. Backend логирование

#### Логирование
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response
```

---

## 🔄 CI/CD Pipeline

### 1. GitHub Actions

#### .github/workflows/ci.yml
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run test
      - run: cd frontend && npm run build

  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && python -m pytest
      - run: cd backend && flake8 .

  deploy:
    needs: [test-frontend, test-backend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Деплой скрипт
          echo "Deploying to production..."
```

---

## 🎯 Будущие улучшения

### 1. Микросервисная архитектура

```
┌─────────────────┐
│   API Gateway   │
└─────────────────┘
          │
    ┌─────┴─────┐
    │           │
┌───▼───┐   ┌───▼───┐
│ Auth  │   │ Users │
│Service│   │Service│
└───────┘   └───────┘
    │           │
┌───▼───┐   ┌───▼───┐
│Request│   │Finance│
│Service│   │Service│
└───────┘   └───────┘
```

### 2. Кеширование

```
┌─────────────────┐
│     Redis       │
│   (Cache)       │
└─────────────────┘
          │
┌─────────────────┐
│   Application   │
│   (Backend)     │
└─────────────────┘
          │
┌─────────────────┐
│   PostgreSQL    │
│   (Database)    │
└─────────────────┘
```

### 3. Очереди сообщений

```
┌─────────────────┐    ┌─────────────────┐
│   Producer      │───▶│   RabbitMQ      │
│   (API)         │    │   (Queue)       │
└─────────────────┘    └─────────────────┘
                               │
                       ┌───────▼───────┐
                       │   Consumer    │

---

## 🔗 Интеграции и автоматизация

### 1. Mango Office Webhook

**Назначение:** Автоматическое создание заявок при входящих звонках

**Архитектура:**
```
┌─────────────────┐    HTTP POST    ┌─────────────────┐
│   Mango Office  │ ──────────────► │   Backend API   │
│   (PBX)         │                │   /mango/webhook │
└─────────────────┘                └─────────────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │   Request       │
                                  │   Creation      │
                                  └─────────────────┘
```

**Особенности:**
- Защита от дублирования заявок (30-минутное окно)
- Автоматическое определение типа заявки ("Впервые"/"Повтор")
- Связывание с рекламными кампаниями по номеру телефона
- Обработка ошибок с откатом транзакций

### 2. Система записей звонков

**Назначение:** Автоматическая загрузка и привязка записей звонков к заявкам

**Архитектура:**
```
┌─────────────────┐    IMAP    ┌─────────────────┐
│   Rambler Mail  │ ◄────────► │   Email Client  │
│   (Storage)     │            │   Service       │
└─────────────────┘            └─────────────────┘
                                       │
                                       ▼
                               ┌─────────────────┐
                               │   File          │
                               │   Processing    │
                               └─────────────────┘
                                       │
                                       ▼
                               ┌─────────────────┐
                               │   Request       │
                               │   Linking       │
                               └─────────────────┘
```

**Компоненты:**
- `EmailClient` - IMAP клиент для Rambler
- `RecordingService` - Фоновый сервис обработки
- `RequestLinking` - Связывание записей с заявками

**Формат файлов:** `YYYY.MM.DD__HH-MM-SS__from_number__to_number.ext`

### 3. Колл-центр интерфейс

**Назначение:** Специализированный интерфейс для сотрудников колл-центра

**Ограничения доступа:**
- Только 3 страницы: Заявки, Входящие заявки, Отчет КЦ
- Скрытие кнопок "Касса" и "Отчеты"
- Фильтрация данных по правам доступа

**Функциональность:**
- Статистика по заявкам
- Фильтрация по городам, статусам, датам
- Экспорт данных в CSV
- Просмотр детальной информации по заявкам
                       │   (Worker)    │
                       └───────────────┘
```

---

## 📚 Заключение

Архитектура проекта построена с учетом современных подходов и лучших практик:

✅ **Разделение ответственности** - четкое разделение на frontend и backend  
✅ **Типизация** - использование TypeScript для безопасности  
✅ **Современные технологии** - актуальные версии фреймворков  
✅ **Безопасность** - JWT, валидация, защита от атак  
✅ **Производительность** - асинхронность, кеширование, оптимизации  
✅ **Масштабируемость** - готовность к росту нагрузки  
✅ **Сопровождение** - качественный код, документация, мониторинг  

Проект готов к production использованию и дальнейшему развитию. 