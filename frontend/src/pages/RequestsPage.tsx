import React, { useState, useMemo, useCallback } from 'react';
import {
  FunnelIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  UserIcon,
  PhoneIcon,
  MapPinIcon,
  CalendarIcon,
  BanknotesIcon,
  WrenchScrewdriverIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Input,
  Button,
  Badge,
  Chip,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Spinner,
  Select,
  SelectItem
} from '@heroui/react';
import { requestsApi, type Request, type Master } from '../api/requests';
import { usersApi } from '../api/users';
import { advertisingCampaignsApi } from '../api/advertisingCampaigns';
import { useAuth } from '../contexts/AuthContext';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData, useMultipleApiData } from '../hooks/useApiData';
import type { RequestStatus } from '../types/api';

interface RequestFilters {
  status?: RequestStatus | '' | undefined;
  city_id?: number;
  request_type_id?: number;
  direction_id?: number;
  master_id?: number;
  advertising_campaign_id?: number;
  search?: string;
}

export const RequestsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { cities, requestTypes, directions, loading: appDataLoading } = useAppData();
  
  // Фильтры
  const [filters, setFilters] = useState<RequestFilters>({
    status: '',
    city_id: undefined,
    request_type_id: undefined,
    direction_id: undefined,
    master_id: undefined,
    advertising_campaign_id: undefined,
    search: ''
  });

  // Загрузка основных данных
  const fetchRequests = useCallback(() => requestsApi.getRequests(filters), [filters]);
  const { 
    data: requestsData, 
    loading: requestsLoading,
    error: requestsError
  } = useApiData(fetchRequests, {
    errorMessage: 'Ошибка загрузки заявок'
  });

  // Загрузка дополнительных данных
  const additionalApiCalls = useMemo(() => ({
    masters: () => usersApi.getMasters(),
    advertisingCampaigns: () => advertisingCampaignsApi.getAdvertisingCampaigns()
  }), []);
  
  const { 
    data: additionalData,
    loading: additionalLoading 
  } = useMultipleApiData(additionalApiCalls, {
    errorMessage: 'Ошибка загрузки дополнительных данных'
  });

  // Мемоизированные данные
  const requests = useMemo(() => requestsData || [], [requestsData]);
  const masters = useMemo(() => additionalData?.masters || [], [additionalData?.masters]);
  const advertisingCampaigns = useMemo(() => additionalData?.advertisingCampaigns || [], [additionalData?.advertisingCampaigns]);

  // Общий индикатор загрузки
  const isLoading = requestsLoading || additionalLoading || appDataLoading.cities || appDataLoading.requestTypes || appDataLoading.directions;

  // Обработчики фильтров
  const handleFilterChange = useCallback((key: keyof RequestFilters, value: string | number | undefined) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === '' ? undefined : value
    }));
  }, []);

  const handleSearch = useCallback((value: string) => {
    handleFilterChange('search', value);
  }, [handleFilterChange]);

  // Фильтрация заявок
  const filteredRequests = useMemo(() => {
    let result = requests;

    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      result = result.filter(request => 
        request.client_name.toLowerCase().includes(searchTerm) ||
        request.client_phone.includes(searchTerm) ||
        request.address?.toLowerCase().includes(searchTerm)
      );
    }

    if (filters.status && filters.status !== '') {
      result = result.filter(request => request.status === filters.status);
    }

    if (filters.city_id) {
      result = result.filter(request => request.city_id === filters.city_id);
    }

    if (filters.master_id) {
      result = result.filter(request => request.master_id === filters.master_id);
    }

    return result;
  }, [requests, filters]);

  // Обработчики действий
  const handleRowClick = useCallback((requestId: number) => {
    navigate(`/requests/${requestId}`);
  }, [navigate]);

  const handleCreateRequest = useCallback(() => {
    navigate('/incoming-requests/create');
  }, [navigate]);

  // Вспомогательные функции
  const getStatusColor = useCallback((status: string) => {
    const statusColors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger'> = {
      'new': 'primary',
      'pending': 'warning', 
      'in_progress': 'secondary',
      'done': 'success',
      'completed': 'success',
      'cancelled': 'danger'
    };
    return statusColors[status] || 'default';
  }, []);

  const getStatusText = useCallback((status: string) => {
    const statusTexts: Record<string, string> = {
      'new': 'Новая',
      'pending': 'Ожидает', 
      'in_progress': 'В работе',
      'done': 'Выполнена',
      'completed': 'Завершена',
      'cancelled': 'Отменена'
    };
    return statusTexts[status] || status;
  }, []);

  const formatDate = useCallback((dateString: string) => {
    return dateString ? new Date(dateString).toLocaleDateString('ru-RU') : '-';
  }, []);

  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

  // Подсчет статистики
  const stats = useMemo(() => {
    return {
      total: filteredRequests.length,
      new: filteredRequests.filter(r => r.status === 'new').length,
      inProgress: filteredRequests.filter(r => r.status === 'in_progress').length,
      completed: filteredRequests.filter(r => ['done', 'completed'].includes(r.status)).length,
      cancelled: filteredRequests.filter(r => r.status === 'cancelled').length
    };
  }, [filteredRequests]);

  // Отображение загрузки
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  // Отображение ошибки
  if (requestsError) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="bg-red-50 border border-red-200">
          <div className="p-4 text-red-700">{requestsError}</div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Заявки</h1>
            <p className="mt-2 text-gray-600">Управление заявками клиентов</p>
          </div>
          <Button
            color="primary"
            startContent={<DocumentTextIcon className="w-5 h-5" />}
            onPress={handleCreateRequest}
          >
            Новая заявка
          </Button>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <Card className="p-4">
          <div className="flex items-center">
            <DocumentTextIcon className="w-8 h-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Всего</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Новые</p>
              <p className="text-2xl font-bold text-blue-600">{stats.new}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">В работе</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.inProgress}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Выполнено</p>
              <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Отменено</p>
              <p className="text-2xl font-bold text-red-600">{stats.cancelled}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Фильтры */}
      <Card className="p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <FunnelIcon className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-medium">Фильтры</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Input
            placeholder="Поиск по имени, телефону, адресу..."
            startContent={<MagnifyingGlassIcon className="w-4 h-4 text-gray-500" />}
            value={filters.search || ''}
            onValueChange={handleSearch}
            isClearable
          />
          
          <Select
            placeholder="Статус"
            selectedKeys={filters.status ? [filters.status] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string;
              handleFilterChange('status', value);
            }}
          >
            <SelectItem key="new">Новая</SelectItem>
            <SelectItem key="pending">Ожидает</SelectItem>
            <SelectItem key="in_progress">В работе</SelectItem>
            <SelectItem key="done">Выполнена</SelectItem>
            <SelectItem key="completed">Завершена</SelectItem>
            <SelectItem key="cancelled">Отменена</SelectItem>
          </Select>
          
          <Select
            placeholder="Город"
            selectedKeys={filters.city_id ? [filters.city_id.toString()] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string;
              handleFilterChange('city_id', value ? parseInt(value) : undefined);
            }}
          >
            {cities.map((city) => (
              <SelectItem key={city.id.toString()}>
                {city.name}
              </SelectItem>
            ))}
          </Select>
          
          <Select
            placeholder="Мастер"
            selectedKeys={filters.master_id ? [filters.master_id.toString()] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string;
              handleFilterChange('master_id', value ? parseInt(value) : undefined);
            }}
          >
            {masters.map((master) => (
              <SelectItem key={master.id.toString()}>
                {master.full_name}
              </SelectItem>
            ))}
          </Select>
        </div>
      </Card>

      {/* Таблица заявок */}
      <Card>
        <Table 
          aria-label="Таблица заявок"
          classNames={{
            wrapper: "min-h-[400px]",
          }}
        >
          <TableHeader>
            <TableColumn>
              <div className="flex items-center gap-2">
                <UserIcon className="w-4 h-4" />
                КЛИЕНТ
              </div>
            </TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <PhoneIcon className="w-4 h-4" />
                ТЕЛЕФОН
              </div>
            </TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <MapPinIcon className="w-4 h-4" />
                АДРЕС
              </div>
            </TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <CalendarIcon className="w-4 h-4" />
                ДАТА
              </div>
            </TableColumn>
            <TableColumn>СТАТУС</TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <WrenchScrewdriverIcon className="w-4 h-4" />
                МАСТЕР
              </div>
            </TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <BanknotesIcon className="w-4 h-4" />
                СУММА
              </div>
            </TableColumn>
          </TableHeader>
          <TableBody>
            {filteredRequests.map((request) => (
              <TableRow 
                key={request.id}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleRowClick(request.id)}
              >
                <TableCell>
                  <div>
                    <div className="font-medium">{request.client_name}</div>
                    <div className="text-sm text-gray-500">{request.city.name}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="font-mono">{request.client_phone}</div>
                </TableCell>
                <TableCell>
                  <div className="max-w-xs truncate">{request.address || '-'}</div>
                </TableCell>
                <TableCell>
                  <div>
                    <div>{formatDate(request.created_at)}</div>
                    {request.meeting_date && (
                      <div className="text-sm text-gray-500">
                        Встреча: {formatDate(request.meeting_date)}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <Chip
                    color={getStatusColor(request.status)}
                    size="sm"
                    variant="flat"
                  >
                    {getStatusText(request.status)}
                  </Chip>
                </TableCell>
                <TableCell>
                  {request.master ? (
                    <div>
                      <div className="font-medium">{request.master.full_name}</div>
                      <div className="text-sm text-gray-500">{request.master.phone_number}</div>
                    </div>
                  ) : (
                    <Badge color="warning" variant="flat">Не назначен</Badge>
                  )}
                </TableCell>
                <TableCell>
                  <div>
                    {request.net_amount > 0 ? (
                      <div className="font-medium text-green-600">
                        {formatCurrency(request.net_amount)}
                      </div>
                    ) : (
                      <div className="text-gray-500">-</div>
                    )}
                    {request.expenses > 0 && (
                      <div className="text-sm text-red-500">
                        Расходы: {formatCurrency(request.expenses)}
                      </div>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}; 