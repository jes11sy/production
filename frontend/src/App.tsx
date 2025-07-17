import React from 'react'
import { Routes, Route, Link as RouterLink, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Button, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Avatar } from '@heroui/react'
import { useAuth } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import { AppDataProvider } from './contexts/AppDataContext'
import Login from './pages/Login';
import Dashboard from './pages/Dashboard'
import { RequestsPage } from './pages/RequestsPage'
import RequestViewPage from './pages/RequestViewPage'
import IncomingRequestsPage from './pages/IncomingRequestsPage';
import IncomingRequestCreatePage from './pages/IncomingRequestCreatePage';
import IncomingRequestEditPage from './pages/IncomingRequestEditPage';
import AdvertisingCampaignsPage from './pages/AdvertisingCampaignsPage';
import MastersPage from './pages/MastersPage';
import MasterCreatePage from './pages/MasterCreatePage';
import MasterViewPage from './pages/MasterViewPage';
import TransactionsPage from './pages/TransactionsPage';
import TransactionCreatePage from './pages/TransactionCreatePage';
import TransactionViewPage from './pages/TransactionViewPage';
import CashBalancePage from './pages/CashBalancePage';
import CashExpensePage from './pages/CashExpensePage';
import CashIncomePage from './pages/CashIncomePage';
import ReportsCitiesPage from './pages/ReportsCitiesPage';
import ReportsMastersPage from './pages/ReportsMastersPage';
import ReportsAdvertisingPage from './pages/ReportsAdvertisingPage';
import UsersPage from './pages/UsersPage';
import { Bars3Icon } from '@heroicons/react/24/outline';
import './App.css';
import logo from './assets/logo.png';
import { ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import CashExpenseAddPage from './pages/CashExpenseAddPage';
import CashIncomeAddPage from './pages/CashIncomeAddPage';
import EmployeeCreatePage from './pages/EmployeeCreatePage';
import CallCenterReportPage from './pages/CallCenterReportPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  const { user, isAuthenticated, isLoading, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  // Удаляю useState и useEffect для dark

  const navigation = [
    { name: 'Дашборд', href: '/' },
    { name: 'Заявки', href: '/requests' },
    { name: 'Входящие заявки', href: '/incoming-requests' },
    { name: 'РК', href: '/advertising-campaigns' },
    { name: 'Мастера', href: '/masters' },
    { name: 'Транзакции', href: '/transactions' },
    { name: 'Пользователи', href: '/users' },
  ];

  // Меню для директора
  const directorNavigation = [
    { name: 'Заявки', href: '/requests' },
    { name: 'Мастера', href: '/masters' },
    { name: 'Транзакции', href: '/transactions' },
    // { name: 'Баланс', href: '/cash/balance' }, // УДАЛЕНО
    // { name: 'Расход', href: '/cash/expense' }, // УДАЛЕНО
    // { name: 'Приход', href: '/cash/income' }, // УДАЛЕНО
    // { name: 'Отчёт по городам', href: '/reports/cities' }, // Уже удалено
    // { name: 'Отчёт по мастерам', href: '/reports/masters' }, // Уже удалено
    // { name: 'Отчёт по рекламе', href: '/reports/advertising' }, // Уже удалено
  ];

  // Меню для колл-центра
  const callcenterNavigation = [
    { name: 'Заявки', href: '/requests' },
    { name: 'Входящие заявки', href: '/incoming-requests' },
    { name: 'Отчет КЦ', href: '/callcenter-report' },
  ];

  // Показываем загрузочный экран пока проверяется аутентификация
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-xl">Загрузка...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <NotificationProvider>
      <AppDataProvider>
        <div>
        <nav className="fixed top-0 left-0 w-full z-50 bg-white shadow-md border-b border-gray-200 px-4 py-2 flex items-center justify-between" style={{ minHeight: 64 }}>
        <div className="flex items-center gap-4">
          <img src={logo} alt="Логотип" style={{ height: 48, width: 'auto', display: 'block' }} />
          <span className="font-medium text-2xl" style={{ color: '#18412b', lineHeight: 1 }}>
            CRM
          </span>
        </div>
        <div className="flex items-center justify-center w-full">
          <div className="bg-gray-100 rounded-full px-2 py-1 flex items-center gap-1">
            {(user?.role === 'director' ? directorNavigation : 
              user?.role === 'callcentr' ? callcenterNavigation : 
              navigation).map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <RouterLink
                  to={item.href}
                  key={item.name}
                  className={
                    isActive
                      ? "px-7 py-2 rounded-full bg-[#18412b] text-white shadow transition-all duration-200"
                      : "px-7 py-2 rounded-full text-gray-800 bg-transparent hover:text-[#18412b] transition-all duration-200"
                  }
                  style={{ minWidth: 120, textAlign: "center" }}
                >
                  {item.name}
                </RouterLink>
              );
            })}
            {/* Скрываем кнопки Касса и Отчеты для callcenter */}
            {user?.role !== 'callcenter' && user?.role !== 'callcentr' && (
              <>
                <Dropdown placement="bottom">
                  <DropdownTrigger>
                    <Button
                      variant="light"
                      className={
                        location.pathname.startsWith('/cash')
                          ? "px-7 py-2 rounded-full bg-[#18412b] text-white shadow transition-all duration-200"
                          : "px-7 py-2 rounded-full text-gray-800 bg-transparent hover:text-[#18412b] transition-all duration-200"
                      }
                      style={{ minWidth: 120, textAlign: "center" }}
                    >
                      Касса
                    </Button>
                  </DropdownTrigger>
                  <DropdownMenu aria-label="Касса">
                    <DropdownItem key="balance" onClick={() => navigate('/cash/balance')}>
                      Баланс
                    </DropdownItem>
                    <DropdownItem key="expense" onClick={() => navigate('/cash/expense')}>
                      Расход
                    </DropdownItem>
                    <DropdownItem key="income" onClick={() => navigate('/cash/income')}>
                      Приход
                    </DropdownItem>
                  </DropdownMenu>
                </Dropdown>
                <Dropdown placement="bottom">
                  <DropdownTrigger>
                    <Button
                      variant="light"
                      className={
                        location.pathname.startsWith('/reports')
                          ? "px-7 py-2 rounded-full bg-[#18412b] text-white shadow transition-all duration-200"
                          : "px-7 py-2 rounded-full text-gray-800 bg-transparent hover:text-[#18412b] transition-all duration-200"
                      }
                      style={{ minWidth: 120, textAlign: "center" }}
                    >
                      Отчеты
                    </Button>
                  </DropdownTrigger>
                  <DropdownMenu aria-label="Отчеты">
                    <DropdownItem key="cities" onClick={() => navigate('/reports/cities')}>
                      Отчет по городам
                    </DropdownItem>
                    <DropdownItem key="masters" onClick={() => navigate('/reports/masters')}>
                      Отчет по мастерам
                    </DropdownItem>
                    <DropdownItem key="advertising" onClick={() => navigate('/reports/advertising')}>
                      Отчет по рекламе
                    </DropdownItem>
                  </DropdownMenu>
                </Dropdown>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Удаляю кнопку переключения темы */}
          <div className="hidden md:block h-8 border-l border-gray-300 mx-2" />
          <Dropdown placement="bottom-end">
            <DropdownTrigger>
              <div className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded transition">
                <Avatar
                  isBordered
                  as="button"
                  className="transition-transform"
                  color="primary"
                  name={user?.login || 'Пользователь'}
                  size="sm"
                />
                <span className="font-medium text-gray-700 text-base hidden sm:block">{user?.login}</span>
              </div>
            </DropdownTrigger>
            <DropdownMenu aria-label="Profile Actions" variant="flat">
              <DropdownItem key="profile" className="py-2 px-3" isDisabled>
                <div>
                  <span className="block text-xs text-gray-400 mb-0.5">Вошли как</span>
                  <span className="block font-semibold text-gray-800">{user?.login || '—'}</span>
                </div>
              </DropdownItem>
              <DropdownItem
                key="logout"
                color="danger"
                onClick={logout}
                startContent={<ArrowRightOnRectangleIcon className="h-5 w-5 text-gray-500" />}
                className="py-2 px-3"
              >
                Выйти
              </DropdownItem>
            </DropdownMenu>
          </Dropdown>
          <button className="md:hidden ml-2 p-2 rounded hover:bg-gray-100" onClick={() => setMobileMenuOpen(v => !v)}>
            <Bars3Icon className="h-6 w-6" />
          </button>
        </div>
        {mobileMenuOpen && (
          <div className="absolute top-full left-0 w-full bg-white shadow-md border-b border-gray-200 flex flex-col items-center py-2 md:hidden animate-fade-in z-50">
            {navigation.map((item) => (
              <RouterLink
                to={item.href}
                key={item.name}
                className={
                  location.pathname === item.href
                    ? "relative navbar-link block w-full text-center py-2 bg-gradient-to-r from-blue-500 to-blue-400 text-white font-extrabold shadow before:content-[''] before:absolute before:top-0 before:left-0 before:w-full before:h-1/2 before:rounded-t-full before:bg-white/20 before:pointer-events-none"
                    : "navbar-link block w-full text-center py-2 text-gray-800 font-bold bg-transparent hover:text-blue-600"
                }
                onClick={() => setMobileMenuOpen(false)}
                style={{ minWidth: 120 }}
              >
                {item.name}
              </RouterLink>
            ))}
          </div>
        )}
      </nav>
      <div className="pt-20 px-2 md:px-0 w-full bg-gray-50 min-h-screen transition-colors duration-300">
        <Routes>
          {user?.role === 'director' ? (
            <>
              <Route path="/requests" element={<ProtectedRoute><RequestsPage /></ProtectedRoute>} />
              <Route path="/requests/new" element={<Navigate to="/incoming-requests/create" replace />} />
              <Route path="/requests/:id" element={<ProtectedRoute><RequestViewPage /></ProtectedRoute>} />
              <Route path="/masters" element={<ProtectedRoute><MastersPage /></ProtectedRoute>} />
              <Route path="/masters/create" element={<ProtectedRoute><MasterCreatePage /></ProtectedRoute>} />
              <Route path="/transactions" element={<ProtectedRoute><TransactionsPage /></ProtectedRoute>} />
              <Route path="/cash/balance" element={<ProtectedRoute><CashBalancePage /></ProtectedRoute>} />
              <Route path="/cash/expense" element={<ProtectedRoute><CashExpensePage /></ProtectedRoute>} />
              <Route path="/cash/income" element={<ProtectedRoute><CashIncomePage /></ProtectedRoute>} />
              <Route path="/cash/expense/add" element={<ProtectedRoute><CashExpenseAddPage /></ProtectedRoute>} />
              <Route path="/cash/income/add" element={<ProtectedRoute><CashIncomeAddPage /></ProtectedRoute>} />
              <Route path="/reports/cities" element={<ProtectedRoute><ReportsCitiesPage /></ProtectedRoute>} />
              <Route path="/reports/masters" element={<ProtectedRoute><ReportsMastersPage /></ProtectedRoute>} />
              <Route path="/reports/advertising" element={<ProtectedRoute><ReportsAdvertisingPage /></ProtectedRoute>} />
              <Route path="*" element={<Navigate to='/requests' replace />} />
            </>
          ) : user?.role === 'callcenter' ? (
            <>
              <Route path="/requests" element={<ProtectedRoute><RequestsPage /></ProtectedRoute>} />
              <Route path="/requests/new" element={<Navigate to="/incoming-requests/create" replace />} />
              <Route path="/requests/:id" element={<ProtectedRoute><RequestViewPage /></ProtectedRoute>} />
              <Route path="/incoming-requests" element={<ProtectedRoute><IncomingRequestsPage /></ProtectedRoute>} />
              <Route path="/incoming-requests/create" element={<ProtectedRoute><IncomingRequestCreatePage /></ProtectedRoute>} />
              <Route path="/incoming-requests/:id/edit" element={<ProtectedRoute><IncomingRequestEditPage /></ProtectedRoute>} />
              <Route path="/callcenter-report" element={<ProtectedRoute><CallCenterReportPage /></ProtectedRoute>} />
              <Route path="*" element={<Navigate to='/requests' replace />} />
            </>
          ) :
            <>
              <Route path="/login" element={<Navigate to="/" replace />} />
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/requests" element={<ProtectedRoute><RequestsPage /></ProtectedRoute>} />
              <Route path="/requests/new" element={<Navigate to="/incoming-requests/create" replace />} />
              <Route path="/requests/:id" element={<ProtectedRoute><RequestViewPage /></ProtectedRoute>} />
              <Route path="/incoming-requests" element={<ProtectedRoute><IncomingRequestsPage /></ProtectedRoute>} />
              <Route path="/incoming-requests/create" element={<ProtectedRoute><IncomingRequestCreatePage /></ProtectedRoute>} />
              <Route path="/incoming-requests/:id/edit" element={<ProtectedRoute><IncomingRequestEditPage /></ProtectedRoute>} />
              <Route path="/advertising-campaigns" element={<ProtectedRoute><AdvertisingCampaignsPage /></ProtectedRoute>} />
              <Route path="/masters" element={<ProtectedRoute><MastersPage /></ProtectedRoute>} />
              <Route path="/masters/create" element={<ProtectedRoute><MasterCreatePage /></ProtectedRoute>} />
              <Route path="/masters/:id" element={<ProtectedRoute><MasterViewPage /></ProtectedRoute>} />
              <Route path="/transactions" element={<ProtectedRoute><TransactionsPage /></ProtectedRoute>} />
              <Route path="/transactions/create" element={<ProtectedRoute><TransactionCreatePage /></ProtectedRoute>} />
              <Route path="/transactions/:id" element={<ProtectedRoute><TransactionViewPage /></ProtectedRoute>} />
              <Route path="/cash/balance" element={<ProtectedRoute><CashBalancePage /></ProtectedRoute>} />
              <Route path="/cash/expense" element={<ProtectedRoute><CashExpensePage /></ProtectedRoute>} />
              <Route path="/cash/income" element={<ProtectedRoute><CashIncomePage /></ProtectedRoute>} />
              <Route path="/cash/expense/add" element={<ProtectedRoute><CashExpenseAddPage /></ProtectedRoute>} />
              <Route path="/cash/income/add" element={<ProtectedRoute><CashIncomeAddPage /></ProtectedRoute>} />
              <Route path="/reports/cities" element={<ProtectedRoute><ReportsCitiesPage /></ProtectedRoute>} />
              <Route path="/reports/masters" element={<ProtectedRoute><ReportsMastersPage /></ProtectedRoute>} />
              <Route path="/reports/advertising" element={<ProtectedRoute><ReportsAdvertisingPage /></ProtectedRoute>} />
              <Route path="/users" element={<ProtectedRoute><UsersPage /></ProtectedRoute>} />
              <Route path="/users/employees/create" element={<ProtectedRoute><EmployeeCreatePage /></ProtectedRoute>} />
              <Route path="*" element={<Navigate to='/' replace />} />
            </>
          }
        </Routes>
        </div>
        </div>
      </AppDataProvider>
    </NotificationProvider>
  )
}

export default App
