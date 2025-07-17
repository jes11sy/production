import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Input,
  Button,
  Select,
  SelectItem,
  Card,
  Chip,
  Tabs,
  Tab,
  Spinner,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure
} from '@heroui/react';
import { 
  PlusIcon, 
  MagnifyingGlassIcon, 
  PencilIcon, 
  TrashIcon, 
  EyeIcon,
  UsersIcon,
  UserCircleIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { usersApi } from '../api/users';
import { useApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { useNotification } from '../contexts/NotificationContext';
import type { Master, Employee, Administrator } from '../types/api';

// Интерфейс для фильтров
interface UsersFilters {
  search: string;
  city_id: string;
  role_id: string;
}

type UserType = Master | Employee | Administrator;
type UserTab = 'masters' | 'employees' | 'administrators';

const UsersPage: React.FC = () => {
  const navigate = useNavigate();
  const { cities, roles } = useAppData();
  const { showSuccess, showError } = useNotification();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const [activeTab, setActiveTab] = useState<UserTab>('masters');
  const [filters, setFilters] = useState<UsersFilters>({
    search: '',
    city_id: '',
    role_id: ''
  });
  const [userToDelete, setUserToDelete] = useState<UserType | null>(null);

  // Функция для загрузки пользователей в зависимости от активной вкладки
  const getUsersFunction = useCallback((): Promise<UserType[]> => {
    switch (activeTab) {
      case 'masters':
        return usersApi.getMasters();
      case 'employees':
        return usersApi.getEmployees();
      case 'administrators':
        return usersApi.getAdministrators();
      default:
        return Promise.resolve([]);
    }
  }, [activeTab]);

  // Загрузка пользователей с автоматическим обновлением при смене вкладки
  const { 
    data: usersData, 
    loading: usersLoading, 
    refetch: refetchUsers 
  } = useApiData<UserType[]>(getUsersFunction, {
    errorMessage: 'Ошибка загрузки пользователей'
  });

  // Мемоизированная фильтрация пользователей
  const filteredUsers = useMemo(() => {
    if (!usersData) return [];
    
    let filtered = [...usersData];
    
    // Фильтр по поиску
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(user => {
        const loginMatch = user.login.toLowerCase().includes(searchTerm);
        const nameMatch = ('full_name' in user && user.full_name?.toLowerCase().includes(searchTerm)) ||
                         ('name' in user && user.name?.toLowerCase().includes(searchTerm));
        return loginMatch || nameMatch;
      });
    }
    
    // Фильтр по городу
    if (filters.city_id) {
      filtered = filtered.filter(user => 
        'city_id' in user && user.city_id === Number(filters.city_id)
      );
    }
    
    // Фильтр по роли
    if (filters.role_id) {
      filtered = filtered.filter(user => 
        'role_id' in user && user.role_id === Number(filters.role_id)
      );
    }
    
    return filtered;
  }, [usersData, filters]);

  // Статистика пользователей
  const userStats = useMemo(() => {
    if (!filteredUsers) return { total: 0, active: 0, inactive: 0 };
    
    const active = filteredUsers.filter(user => user.status === 'active').length;
    const inactive = filteredUsers.length - active;
    
    return {
      total: filteredUsers.length,
      active,
      inactive
    };
  }, [filteredUsers]);

  // Мемоизированные обработчики
  const handleFilterChange = useCallback((key: keyof UsersFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleTabChange = useCallback((key: React.Key) => {
    setActiveTab(key as UserTab);
    // Сбрасываем фильтры при смене вкладки
    setFilters({
      search: '',
      city_id: '',
      role_id: ''
    });
  }, []);

  const confirmDelete = useCallback((user: UserType) => {
    setUserToDelete(user);
    onOpen();
  }, [onOpen]);

  const handleDelete = useCallback(async () => {
    if (!userToDelete) return;
    
    try {
      if (activeTab === 'masters') {
        await usersApi.deleteMaster(userToDelete.id);
        showSuccess('Мастер успешно удален');
      } else if (activeTab === 'employees') {
        await usersApi.deleteEmployee(userToDelete.id);
        showSuccess('Сотрудник успешно удален');
      } else if (activeTab === 'administrators') {
        await usersApi.deleteAdministrator(userToDelete.id);
        showSuccess('Администратор успешно удален');
      }
      
      await refetchUsers();
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Ошибка удаления пользователя';
      showError(message);
      console.error('Delete error:', error);
    } finally {
      onClose();
      setUserToDelete(null);
    }
  }, [userToDelete, showSuccess, showError, refetchUsers, onClose]);

  // Вспомогательные функции
  const getCreatePath = useCallback(() => {
    switch (activeTab) {
      case 'employees':
        return '/users/employees/create';
      case 'masters':
        return '/users/masters/create';
      case 'administrators':
        return '/users/administrators/create';
      default:
        return '/users/masters/create';
    }
  }, [activeTab]);

  const getCityName = useCallback((user: UserType) => {
    if ('city' in user && user.city?.name) return user.city.name;
    if ('city_id' in user && user.city_id) {
      const city = cities.find(c => c.id === user.city_id);
      return city ? city.name : 'Неизвестно';
    }
    return 'Неизвестно';
  }, [cities]);

  const getRoleName = useCallback((user: UserType) => {
    if ('role' in user && user.role?.name) return user.role.name;
    if ('role_id' in user && user.role_id) {
      const role = roles.find(r => r.id === user.role_id);
      return role ? role.name : 'Неизвестно';
    }
    return 'Неизвестно';
  }, [roles]);

  const getStatusColor = useCallback((isActive: boolean) => {
    return isActive ? 'success' : 'danger';
  }, []);

  const getStatusText = useCallback((isActive: boolean) => {
    return isActive ? 'Активен' : 'Неактивен';
  }, []);

  const getUserName = useCallback((user: UserType): string => {
    if ('full_name' in user) return user.full_name;
    if ('name' in user) return user.name;
    return '—';
  }, []);

  // Получение иконки для вкладки
  const getTabIcon = useCallback((tab: UserTab) => {
    switch (tab) {
      case 'masters':
        return <UsersIcon className="h-4 w-4" />;
      case 'employees':
        return <UserCircleIcon className="h-4 w-4" />;
      case 'administrators':
        return <ShieldCheckIcon className="h-4 w-4" />;
      default:
        return null;
    }
  }, []);

  // Мемоизированный рендер строки пользователя
  const renderUserRow = useCallback((user: UserType) => (
    <TableRow key={user.id}>
      <TableCell>{user.id}</TableCell>
      <TableCell>{user.login}</TableCell>
      <TableCell>{getUserName(user)}</TableCell>
      <TableCell>{getCityName(user)}</TableCell>
      <TableCell>{getRoleName(user)}</TableCell>
      <TableCell>
        <Chip color={getStatusColor(user.status === 'active')} size="sm">
          {getStatusText(user.status === 'active')}
        </Chip>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Button
            isIconOnly
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/users/${activeTab}/${user.id}`)}
          >
            <EyeIcon className="h-4 w-4" />
          </Button>
          <Button
            isIconOnly
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/users/${activeTab}/${user.id}/edit`)}
          >
            <PencilIcon className="h-4 w-4" />
          </Button>
          <Button
            isIconOnly
            size="sm"
            variant="ghost"
            color="danger"
            onClick={() => confirmDelete(user)}
          >
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  ), [activeTab, navigate, confirmDelete, getUserName, getCityName, getRoleName, getStatusColor, getStatusText]);

  const getTabTitle = useCallback((tab: UserTab) => {
    const titles = {
      masters: 'Мастера',
      employees: 'Сотрудники', 
      administrators: 'Администраторы'
    };
    return titles[tab];
  }, []);

  const getTabLabel = useCallback((tab: UserTab) => {
    const count = tab === activeTab ? userStats.total : 0;
    return (
      <div className="flex items-center gap-2">
        {getTabIcon(tab)}
        <span>{getTabTitle(tab)}</span>
        {tab === activeTab && (
          <Chip size="sm" variant="flat" color="primary">
            {count}
          </Chip>
        )}
      </div>
    );
  }, [activeTab, userStats.total, getTabIcon, getTabTitle]);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-4">Пользователи</h1>
        
        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <UsersIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Всего</p>
                <p className="text-2xl font-bold">{userStats.total}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <UserCircleIcon className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Активных</p>
                <p className="text-2xl font-bold text-green-600">{userStats.active}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <ShieldCheckIcon className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Неактивных</p>
                <p className="text-2xl font-bold text-red-600">{userStats.inactive}</p>
              </div>
            </div>
          </Card>
        </div>
        
        {/* Фильтры */}
        <Card className="mb-4">
          <div className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <Input
                placeholder="Поиск по ID, имени или логину"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="max-w-xs"
                startContent={<MagnifyingGlassIcon className="h-4 w-4" />}
              />
              
              <Select
                placeholder="Все города"
                selectedKeys={filters.city_id ? [filters.city_id] : []}
                onSelectionChange={(keys) => 
                  handleFilterChange('city_id', Array.from(keys)[0] as string || '')
                }
                className="max-w-xs"
                isLoading={!cities.length}
              >
                {cities.map(city => (
                  <SelectItem key={city.id}>
                    {city.name}
                  </SelectItem>
                ))}
              </Select>
              
              <Select
                placeholder="Все роли"
                selectedKeys={filters.role_id ? [filters.role_id] : []}
                onSelectionChange={(keys) => 
                  handleFilterChange('role_id', Array.from(keys)[0] as string || '')
                }
                className="max-w-xs"
                isLoading={!roles.length}
              >
                {roles.map(role => (
                  <SelectItem key={role.id}>
                    {role.name}
                  </SelectItem>
                ))}
              </Select>
              
              <Button
                color="primary"
                onClick={() => navigate(getCreatePath())}
                startContent={<PlusIcon className="h-4 w-4" />}
              >
                Создать пользователя
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Основная таблица с вкладками */}
      <Card>
        <Tabs
          selectedKey={activeTab}
          onSelectionChange={handleTabChange}
          className="p-4"
        >
          <Tab key="masters" title={getTabLabel('masters')}>
            <div className="mt-4">
              <Table aria-label="Таблица мастеров">
                <TableHeader>
                  <TableColumn>ID</TableColumn>
                  <TableColumn>Логин</TableColumn>
                  <TableColumn>Имя</TableColumn>
                  <TableColumn>Город</TableColumn>
                  <TableColumn>Роль</TableColumn>
                  <TableColumn>Статус</TableColumn>
                  <TableColumn>Действия</TableColumn>
                </TableHeader>
                <TableBody
                  isLoading={usersLoading}
                  loadingContent={<Spinner />}
                  emptyContent="Нет данных"
                >
                  {filteredUsers.map(renderUserRow)}
                </TableBody>
              </Table>
            </div>
          </Tab>
          
          <Tab key="employees" title={getTabLabel('employees')}>
            <div className="mt-4">
              <Table aria-label="Таблица сотрудников">
                <TableHeader>
                  <TableColumn>ID</TableColumn>
                  <TableColumn>Логин</TableColumn>
                  <TableColumn>Имя</TableColumn>
                  <TableColumn>Город</TableColumn>
                  <TableColumn>Роль</TableColumn>
                  <TableColumn>Статус</TableColumn>
                  <TableColumn>Действия</TableColumn>
                </TableHeader>
                <TableBody
                  isLoading={usersLoading}
                  loadingContent={<Spinner />}
                  emptyContent="Нет данных"
                >
                  {filteredUsers.map(renderUserRow)}
                </TableBody>
              </Table>
            </div>
          </Tab>
          
          <Tab key="administrators" title={getTabLabel('administrators')}>
            <div className="mt-4">
              <Table aria-label="Таблица администраторов">
                <TableHeader>
                  <TableColumn>ID</TableColumn>
                  <TableColumn>Логин</TableColumn>
                  <TableColumn>Имя</TableColumn>
                  <TableColumn>Город</TableColumn>
                  <TableColumn>Роль</TableColumn>
                  <TableColumn>Статус</TableColumn>
                  <TableColumn>Действия</TableColumn>
                </TableHeader>
                <TableBody
                  isLoading={usersLoading}
                  loadingContent={<Spinner />}
                  emptyContent="Нет данных"
                >
                  {filteredUsers.map(renderUserRow)}
                </TableBody>
              </Table>
            </div>
          </Tab>
        </Tabs>
      </Card>

      {/* Модал подтверждения удаления */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalContent>
          <ModalHeader>Подтверждение удаления</ModalHeader>
          <ModalBody>
            <p>Вы уверены, что хотите удалить пользователя <strong>{userToDelete?.login}</strong>?</p>
            <p className="text-sm text-gray-600">Это действие нельзя отменить.</p>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onClick={onClose}>
              Отмена
            </Button>
            <Button color="danger" onClick={handleDelete}>
              Удалить
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default UsersPage; 