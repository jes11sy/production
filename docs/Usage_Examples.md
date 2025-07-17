# 📖 Примеры использования системы

## 🎯 Общие сценарии использования

### 1. Роли пользователей

#### Администратор
- Управляет пользователями, городами, ролями
- Просматривает все данные по всем городам
- Настраивает систему

#### Директор
- Управляет мастерами в своем городе
- Просматривает заявки и финансы своего города
- Создает отчеты по своему региону

#### Менеджер
- Обрабатывает входящие заявки
- Назначает мастеров на заявки
- Отслеживает выполнение работ

#### Авитолог
- Управляет рекламными кампаниями
- Создает новые заявки из источников
- Анализирует эффективность рекламы

#### Мастер
- Просматривает назначенные заявки
- Обновляет статус выполнения
- Добавляет результаты работ

---

## 🔐 Вход в систему

### Процесс аутентификации

```javascript
// Frontend: Login.tsx
const handleLogin = async (data: LoginForm) => {
  try {
    await login(data.login, data.password);
    navigate('/dashboard');
  } catch (error) {
    setError('Неверные учетные данные');
  }
};
```

```python
# Backend: auth.py
@router.post("/login")
async def login(
    user_credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, user_credentials.login, user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Установка httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return {"message": "Успешный вход", "user": user}
```

---

## 📝 Управление заявками

### 1. Создание новой заявки

#### Frontend форма
```typescript
// IncomingRequestCreatePage.tsx
const schema = z.object({
  advertising_campaign_id: z.number().optional(),
  city_id: z.number().min(1, 'Выберите город'),
  request_type_id: z.number().min(1, 'Выберите тип заявки'),
  client_phone: z.string().min(1, 'Номер телефона обязателен'),
  client_name: z.string().min(1, 'Имя клиента обязательно'),
  address: z.string().optional(),
  problem: z.string().optional(),
  meeting_date: z.string().optional(),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema)
});

const onSubmit = async (data: RequestForm) => {
  try {
    await requestsApi.createRequest(data);
    navigate('/requests');
  } catch (error) {
    setError('Ошибка создания заявки');
  }
};
```

#### Backend обработка
```python
# api/requests.py
@router.post("/", response_model=RequestResponse)
async def create_request(
    request: RequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверка прав доступа
    if not has_permission(current_user, "create_request"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    # Создание заявки
    db_request = Request(**request.dict())
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    
    return db_request
```

### 2. Назначение мастера на заявку

```typescript
// RequestViewPage.tsx
const assignMaster = async (masterId: number) => {
  try {
    await requestsApi.updateRequest(requestId, {
      master_id: masterId,
      status: 'assigned'
    });
    setRequest(prev => ({
      ...prev,
      master_id: masterId,
      status: 'assigned'
    }));
  } catch (error) {
    setError('Ошибка назначения мастера');
  }
};
```

### 3. Завершение заявки

```typescript
// RequestViewPage.tsx
const completeRequest = async (data: {
  result: string;
  expenses: number;
  net_amount: number;
  master_handover: number;
}) => {
  try {
    await requestsApi.updateRequest(requestId, {
      ...data,
      status: 'done'
    });
    setRequest(prev => ({ ...prev, ...data, status: 'done' }));
  } catch (error) {
    setError('Ошибка завершения заявки');
  }
};
```

---

## 💰 Управление финансами

### 1. Создание транзакции прихода

```typescript
// CashIncomeAddPage.tsx
const createIncomeTransaction = async (data: TransactionForm) => {
  try {
    await transactionsApi.createTransaction({
      city_id: data.city_id,
      transaction_type_id: data.transaction_type_id,
      amount: Math.abs(data.amount), // Приход всегда положительный
      notes: data.notes,
      specified_date: data.specified_date
    });
    navigate('/cash-income');
  } catch (error) {
    setError('Ошибка создания транзакции');
  }
};
```

### 2. Создание транзакции расхода

```typescript
// CashExpenseAddPage.tsx
const createExpenseTransaction = async (data: TransactionForm) => {
  try {
    const transaction = await transactionsApi.createTransaction({
      city_id: data.city_id,
      transaction_type_id: data.transaction_type_id,
      amount: -Math.abs(data.amount), // Расход всегда отрицательный
      notes: data.notes,
      specified_date: data.specified_date
    });
    
    // Загрузка чека расхода
    if (expenseReceipt) {
      await uploadExpenseReceipt(transaction.id, expenseReceipt);
    }
    
    navigate('/cash-expense');
  } catch (error) {
    setError('Ошибка создания транзакции');
  }
};
```

### 3. Просмотр баланса по городам

```typescript
// CashBalancePage.tsx
const calculateCityBalance = (cityId: number) => {
  const cityTransactions = transactions.filter(t => t.city_id === cityId);
  
  const income = cityTransactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);
    
  const expenses = cityTransactions
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);
    
  return {
    income,
    expenses,
    balance: income - expenses
  };
};
```

---

## 👥 Управление пользователями

### 1. Создание нового мастера

```typescript
// MasterCreatePage.tsx
const createMaster = async (data: MasterForm) => {
  try {
    await usersApi.createMaster({
      city_id: data.city_id,
      full_name: data.full_name,
      phone_number: data.phone_number,
      birth_date: data.birth_date,
      passport: data.passport,
      login: data.login,
      password: data.password,
      notes: data.notes
    });
    navigate('/masters');
  } catch (error) {
    setError('Ошибка создания мастера');
  }
};
```

### 2. Создание сотрудника

```typescript
// EmployeeCreatePage.tsx
const createEmployee = async (data: EmployeeForm) => {
  try {
    await usersApi.createEmployee({
      name: data.name,
      role_id: data.role_id,
      city_id: data.city_id,
      login: data.login,
      password: data.password,
      notes: data.notes
    });
    navigate('/users');
  } catch (error) {
    setError('Ошибка создания сотрудника');
  }
};
```

---

## 📊 Отчеты и аналитика

### 1. Отчет по мастерам

```typescript
// ReportsMastersPage.tsx
const generateMasterReport = (master: Master) => {
  const masterRequests = requests.filter(r => r.master_id === master.id);
  
  return {
    id: master.id,
    name: master.full_name,
    city: master.city.name,
    totalRequests: masterRequests.length,
    completedRequests: masterRequests.filter(r => r.status === 'done').length,
    totalIncome: masterRequests
      .filter(r => r.status === 'done')
      .reduce((sum, r) => sum + (r.net_amount || 0), 0),
    totalExpenses: masterRequests
      .reduce((sum, r) => sum + (r.expenses || 0), 0),
    averageHandover: masterRequests.length > 0 
      ? masterRequests.reduce((sum, r) => sum + (r.master_handover || 0), 0) / masterRequests.length
      : 0
  };
};
```

### 2. Отчет по городам

```typescript
// ReportsCitiesPage.tsx
const generateCityReport = (city: City) => {
  const cityRequests = requests.filter(r => r.city_id === city.id);
  const cityTransactions = transactions.filter(t => t.city_id === city.id);
  const cityMasters = masters.filter(m => m.city_id === city.id);
  
  return {
    id: city.id,
    name: city.name,
    totalRequests: cityRequests.length,
    completedRequests: cityRequests.filter(r => r.status === 'done').length,
    totalMasters: cityMasters.length,
    activeMasters: cityMasters.filter(m => m.status === 'active').length,
    totalIncome: cityTransactions
      .filter(t => t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0),
    totalExpenses: cityTransactions
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0)
  };
};
```

### 3. Отчет по рекламным кампаниям

```typescript
// ReportsAdvertisingPage.tsx
const generateCampaignReport = (campaign: AdvertisingCampaign) => {
  const campaignRequests = requests.filter(r => r.advertising_campaign_id === campaign.id);
  
  return {
    id: campaign.id,
    name: campaign.name,
    phone: campaign.phone_number,
    city: campaign.city.name,
    totalRequests: campaignRequests.length,
    completedRequests: campaignRequests.filter(r => r.status === 'done').length,
    conversionRate: campaignRequests.length > 0 
      ? (campaignRequests.filter(r => r.status === 'done').length / campaignRequests.length) * 100
      : 0,
    totalRevenue: campaignRequests
      .filter(r => r.status === 'done')
      .reduce((sum, r) => sum + (r.net_amount || 0), 0),
    averageRevenue: campaignRequests.length > 0
      ? campaignRequests.reduce((sum, r) => sum + (r.net_amount || 0), 0) / campaignRequests.length
      : 0
  };
};
```

---

## 📎 Работа с файлами

### 1. Загрузка файлов

```typescript
// FileUpload component
const uploadFile = async (file: File, type: 'bso' | 'expense' | 'recording') => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch(`/api/v1/upload-${type}/`, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Ошибка загрузки файла');
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
};
```

### 2. Отображение загруженных файлов

```typescript
// FileDisplay component
const FileDisplay = ({ filePath, fileName }: { filePath: string; fileName: string }) => {
  const fullPath = `http://localhost:8000/${filePath.replace(/\\/g, '/')}`;
  
  const isImage = /\.(jpg|jpeg|png|gif)$/i.test(fileName);
  
  if (isImage) {
    return (
      <div className="file-preview">
        <img 
          src={fullPath} 
          alt={fileName}
          className="max-w-xs max-h-48 object-contain"
        />
        <a href={fullPath} target="_blank" rel="noopener noreferrer">
          Открыть в новом окне
        </a>
      </div>
    );
  }
  
  return (
    <div className="file-link">
      <a href={fullPath} target="_blank" rel="noopener noreferrer">
        📎 {fileName}
      </a>
    </div>
  );
};
```

---

## 🔍 Поиск и фильтрация

### 1. Фильтрация заявок

```typescript
// RequestsPage.tsx
const filterRequests = (requests: Request[], filters: {
  search: string;
  status: string;
  city_id: string;
  master_id: string;
}) => {
  let filtered = requests;
  
  // Поиск по тексту
  if (filters.search) {
    filtered = filtered.filter(request =>
      request.client_name.toLowerCase().includes(filters.search.toLowerCase()) ||
      request.client_phone.includes(filters.search) ||
      request.problem?.toLowerCase().includes(filters.search.toLowerCase())
    );
  }
  
  // Фильтр по статусу
  if (filters.status) {
    filtered = filtered.filter(request => request.status === filters.status);
  }
  
  // Фильтр по городу
  if (filters.city_id) {
    filtered = filtered.filter(request => request.city_id === Number(filters.city_id));
  }
  
  // Фильтр по мастеру
  if (filters.master_id) {
    filtered = filtered.filter(request => request.master_id === Number(filters.master_id));
  }
  
  return filtered;
};
```

### 2. Поиск пользователей

```typescript
// UsersPage.tsx
const filterUsers = (users: User[], filters: {
  search: string;
  city_id: string;
  role_id: string;
}) => {
  let filtered = users;
  
  // Поиск по имени
  if (filters.search) {
    filtered = filtered.filter(user =>
      (user as any).first_name?.toLowerCase().includes(filters.search.toLowerCase()) ||
      (user as any).last_name?.toLowerCase().includes(filters.search.toLowerCase()) ||
      (user as any).full_name?.toLowerCase().includes(filters.search.toLowerCase())
    );
  }
  
  // Фильтр по городу
  if (filters.city_id) {
    filtered = filtered.filter(user => 
      (user as any).city_id === Number(filters.city_id)
    );
  }
  
  // Фильтр по роли
  if (filters.role_id) {
    filtered = filtered.filter(user => 
      (user as any).role_id === Number(filters.role_id)
    );
  }
  
  return filtered;
};
```

---

## 🔄 Обновление данных в реальном времени

### 1. Периодическое обновление

```typescript
// Custom hook для автообновления
const useAutoRefresh = (fetchData: () => Promise<void>, interval: number = 30000) => {
  const intervalRef = useRef<NodeJS.Timeout>();
  
  useEffect(() => {
    intervalRef.current = setInterval(fetchData, interval);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, interval]);
  
  const startAutoRefresh = () => {
    if (!intervalRef.current) {
      intervalRef.current = setInterval(fetchData, interval);
    }
  };
  
  const stopAutoRefresh = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
  };
  
  return { startAutoRefresh, stopAutoRefresh };
};

// Использование
const { startAutoRefresh, stopAutoRefresh } = useAutoRefresh(loadData, 30000);
```

### 2. Обновление при изменении статуса

```typescript
// RequestViewPage.tsx
const updateRequestStatus = async (newStatus: string) => {
  try {
    const updatedRequest = await requestsApi.updateRequest(requestId, {
      status: newStatus
    });
    
    setRequest(updatedRequest);
    
    // Уведомление об успешном обновлении
    toast.success('Статус заявки обновлен');
  } catch (error) {
    toast.error('Ошибка обновления статуса');
  }
};
```

---

## 🎨 Настройка интерфейса

### 1. Темная тема

```typescript
// ThemeProvider.tsx
const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);
  
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };
  
  return (
    <div className={theme}>
      <ThemeContext.Provider value={{ theme, toggleTheme }}>
        {children}
      </ThemeContext.Provider>
    </div>
  );
};
```

### 2. Адаптивный дизайн

```typescript
// ResponsiveTable.tsx
const ResponsiveTable = ({ data, columns }: TableProps) => {
  const [isMobile, setIsMobile] = useState(false);
  
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  if (isMobile) {
    return (
      <div className="mobile-cards">
        {data.map((item, index) => (
          <Card key={index} className="mb-4">
            <CardBody>
              {columns.map((column, colIndex) => (
                <div key={colIndex} className="flex justify-between py-1">
                  <span className="font-medium">{column.title}:</span>
                  <span>{column.render ? column.render(item) : item[column.key]}</span>
                </div>
              ))}
            </CardBody>
          </Card>
        ))}
      </div>
    );
  }
  
  return (
    <Table>
      <TableHeader>
        {columns.map((column) => (
          <TableColumn key={column.key}>{column.title}</TableColumn>
        ))}
      </TableHeader>
      <TableBody>
        {data.map((item, index) => (
          <TableRow key={index}>
            {columns.map((column) => (
              <TableCell key={column.key}>
                {column.render ? column.render(item) : item[column.key]}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
```

---

## 🔧 Отладка и разработка

### 1. Логирование действий

```typescript
// Logger utility
const logger = {
  info: (message: string, data?: any) => {
    console.log(`[INFO] ${message}`, data);
  },
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error);
  },
  warn: (message: string, data?: any) => {
    console.warn(`[WARN] ${message}`, data);
  }
};

// Использование в компонентах
const handleSubmit = async (data: FormData) => {
  logger.info('Submitting form', data);
  
  try {
    await submitData(data);
    logger.info('Form submitted successfully');
  } catch (error) {
    logger.error('Form submission failed', error);
  }
};
```

### 2. Отладка API запросов

```typescript
// API interceptor для отладки
axios.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);
```

---

## 📱 Мобильная версия

### 1. Мобильная навигация

```typescript
// MobileNavigation.tsx
const MobileNavigation = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="md:hidden">
      <Button
        variant="ghost"
        onClick={() => setIsOpen(!isOpen)}
        className="p-2"
      >
        <Bars3Icon className="h-6 w-6" />
      </Button>
      
      {isOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white shadow-lg z-50">
          <nav className="flex flex-col p-4">
            <Link to="/dashboard" className="py-2 px-4 hover:bg-gray-100">
              Dashboard
            </Link>
            <Link to="/requests" className="py-2 px-4 hover:bg-gray-100">
              Заявки
            </Link>
            <Link to="/transactions" className="py-2 px-4 hover:bg-gray-100">
              Транзакции
            </Link>
          </nav>
        </div>
      )}
    </div>
  );
};
```

### 2. Адаптивные формы

```typescript
// AdaptiveForm.tsx
const AdaptiveForm = ({ children, ...props }) => {
  return (
    <form 
      className="space-y-4 max-w-md mx-auto md:max-w-lg lg:max-w-2xl"
      {...props}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {children}
      </div>
    </form>
  );
};
```

---

## 🎯 Заключение

Эти примеры показывают основные сценарии использования системы управления заявками. Система поддерживает:

- **Полный цикл обработки заявок** от создания до завершения
- **Управление финансами** с детализацией по городам и типам
- **Ролевую модель** с различными уровнями доступа
- **Отчетность и аналитику** для принятия решений
- **Работу с файлами** для документооборота
- **Адаптивный интерфейс** для работы на разных устройствах

Все компоненты построены с использованием современных паттернов React и TypeScript, обеспечивая надежность и удобство сопровождения кода. 