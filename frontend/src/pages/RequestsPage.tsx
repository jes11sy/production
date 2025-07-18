import React, { useState, useMemo, useCallback } from 'react';
import {
  FunnelIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Input,
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
import { useApiData, useMultipleApiData, useDebouncedValue } from '../hooks/useApiData';
import type { RequestStatus } from '../types/api';

interface RequestFilters {
  status?: RequestStatus | string | undefined;
  city_id?: number;
  request_type_id?: number;
  direction_id?: number;
  master_id?: number;
  advertising_campaign_id?: number;
  search?: string;
}

// Маппинги статусов на русский язык с цветами
const statusMappings = {
  'Ожидает': { text: 'Ожидает', color: 'warning' as const },
  'Ожидает Принятия': { text: 'Ожидает Принятия', color: 'primary' as const },
  'Принял': { text: 'Принял', color: 'secondary' as const },
  'В пути': { text: 'В пути', color: 'secondary' as const },
  'В работе': { text: 'В работе', color: 'primary' as const },
  'Модерн': { text: 'Модерн', color: 'primary' as const },
  'Готово': { text: 'Готово', color: 'success' as const },
  'Отказ': { text: 'Отказ', color: 'danger' as const },
};

// Приоритеты статусов для сортировки
const getStatusPriority = (status: string): number => {
  const priorities: { [key: string]: number } = {
    'Ожидает': 1,
    'Ожидает Принятия': 2,
    'Принял': 3,
    'В пути': 4,
    'В работе': 5,
    'Модерн': 6,
    'Готово': 7,
    'Отказ': 8,
  };
  return priorities[status] || 999;
};

export const RequestsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { cities, requestTypes, directions, loading: appDataLoading } = useAppData();
  
  // Состояние для мгновенного поиска (для UI)
  const [searchInput, setSearchInput] = useState('');
  
  // Debounced значение поиска (для API запросов)
  const debouncedSearch = useDebouncedValue(searchInput, 500);
  
  // Фильтры
  const [filters, setFilters] = useState<RequestFilters>({
    status: undefined,
    city_id: undefined,
    request_type_id: undefined,
    direction_id: undefined,
    master_id: undefined,
    advertising_campaign_id: undefined,
    search: ''
  });

  // Обновляем фильтры когда debounced search изменяется
  React.useEffect(() => {
    setFilters(prev => ({
      ...prev,
      search: debouncedSearch || undefined
    }));
  }, [debouncedSearch]);

  // Загрузка основных данных с актуальными фильтрами
  const fetchRequests = useCallback(() => {
    // Создаем параметры запроса, исключая пустые значения
    const params: any = {};
    
    if (filters.status && filters.status !== '') {
      params.status = filters.status;
    }
    if (filters.city_id) {
      params.city_id = filters.city_id;
    }
    if (filters.master_id) {
      params.master_id = filters.master_id;
    }
    if (filters.search && filters.search.trim()) {
      params.search = filters.search.trim();
    }
    
    return requestsApi.getRequests(params);
  }, [filters]);

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

  const handleSearchInputChange = useCallback((value: string) => {
    setSearchInput(value);
  }, []);

  // Фильтрация и сортировка заявок (теперь делается на фронтенде для дополнительных фильтров)
  const filteredRequests = useMemo(() => {
    let result = requests;

    // Фильтрация по отображаемым статусам
    const allowedStatuses = [
      'Ожидает', 
      'Ожидает Принятия', 
      'Принял', 
      'В пути', 
      'В работе', 
      'Модерн', 
      'Готово', 
      'Отказ'
    ];
    result = result.filter(request => allowedStatuses.includes(request.status));

    // Дополнительная фильтрация по введенному тексту (мгновенная для лучшего UX)
    if (searchInput && searchInput.trim()) {
      const searchTerm = searchInput.toLowerCase();
      result = result.filter(request => 
        request.client_name.toLowerCase().includes(searchTerm) ||
        request.client_phone.includes(searchTerm) ||
        request.address?.toLowerCase().includes(searchTerm) ||
        request.id.toString().includes(searchTerm)
      );
    }

    if (filters.status && filters.status !== undefined) {
      result = result.filter(request => request.status === filters.status);
    }

    if (filters.city_id) {
      result = result.filter(request => request.city_id === filters.city_id);
    }

    if (filters.master_id) {
      result = result.filter(request => request.master_id === filters.master_id);
    }

    // Сортировка по приоритету статусов
    result = result.sort((a, b) => {
      const priorityA = getStatusPriority(a.status);
      const priorityB = getStatusPriority(b.status);
      
      if (priorityA !== priorityB) {
        return priorityA - priorityB;
      }
      
      // Если статусы одинаковые, сортируем по ID (новые сверху)
      return b.id - a.id;
    });

    return result;
  }, [requests, filters, searchInput]);

  // Обработчики действий
  const handleRowClick = useCallback((requestId: number) => {
    navigate(`/requests/${requestId}`);
  }, [navigate]);

  // Вспомогательные функции
  const getStatusColor = useCallback((status: string) => {
    const mapping = statusMappings[status as keyof typeof statusMappings];
    return mapping?.color || 'default';
  }, []);

  const getStatusText = useCallback((status: string) => {
    const mapping = statusMappings[status as keyof typeof statusMappings];
    return mapping?.text || status;
  }, []);

  const formatDate = useCallback((dateString: string) => {
    return dateString ? new Date(dateString).toLocaleDateString('ru-RU') : '-';
  }, []);

  // Отображение загрузки
  if (isLoading && !requests.length) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  // Отображение ошибки
  if (requestsError && !requests.length) {
    return (
      <div className="min-h-screen w-full px-4">
        <Card className="bg-red-50 border border-red-200">
          <div className="p-4 text-red-700">{requestsError}</div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full">
      {/* Заголовок */}
      <div className="mb-4 px-4">
        <h1 className="text-3xl font-bold text-gray-900">Заявки</h1>
        <p className="mt-2 text-gray-600">Управление заявками клиентов</p>
      </div>

      {/* Фильтры */}
      <Card className="mx-4 mb-4 p-4">
        <div className="flex items-center gap-4 mb-4">
          <FunnelIcon className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-medium">Фильтры</h3>
          {requestsLoading && (
            <Spinner size="sm" color="primary" />
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Input
            placeholder="Поиск по ID, имени, телефону, адресу..."
            startContent={<MagnifyingGlassIcon className="w-4 h-4 text-gray-500" />}
            value={searchInput}
            onValueChange={handleSearchInputChange}
            isClearable
            onClear={() => setSearchInput('')}
          />
          
          <Select
            placeholder="Статус"
            selectedKeys={filters.status ? [filters.status] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string;
              handleFilterChange('status', value);
            }}
          >
            <SelectItem key="Ожидает">Ожидает</SelectItem>
            <SelectItem key="Ожидает Принятия">Ожидает Принятия</SelectItem>
            <SelectItem key="Принял">Принял</SelectItem>
            <SelectItem key="В пути">В пути</SelectItem>
            <SelectItem key="В работе">В работе</SelectItem>
            <SelectItem key="Модерн">Модерн</SelectItem>
            <SelectItem key="Готово">Готово</SelectItem>
            <SelectItem key="Отказ">Отказ</SelectItem>
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

      {/* Таблица заявок на весь экран */}
      <div className="px-4">
        <Card className="w-full">
          <Table 
            aria-label="Таблица заявок"
            classNames={{
              wrapper: "min-h-[calc(100vh-300px)] w-full",
              table: "w-full",
            }}
          >
            <TableHeader>
              <TableColumn width="60">ID</TableColumn>
              <TableColumn width="120">РК</TableColumn>
              <TableColumn width="100">ГОРОД</TableColumn>
              <TableColumn width="120">ТИП ЗАЯВКИ</TableColumn>
              <TableColumn width="130">ТЕЛЕФОН</TableColumn>
              <TableColumn width="150">ИМЯ КЛИЕНТА</TableColumn>
              <TableColumn width="200">АДРЕС</TableColumn>
              <TableColumn width="120">ДАТА ВСТРЕЧИ</TableColumn>
              <TableColumn width="120">НАПРАВЛЕНИЕ</TableColumn>
              <TableColumn width="150">ПРОБЛЕМА</TableColumn>
              <TableColumn width="100">СТАТУС</TableColumn>
              <TableColumn width="150">МАСТЕР</TableColumn>
              <TableColumn width="150">ИТОГ</TableColumn>
            </TableHeader>
            <TableBody>
              {filteredRequests.map((request) => (
                <TableRow 
                  key={request.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleRowClick(request.id)}
                >
                  <TableCell>
                    <div className="font-mono text-sm">{request.id}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs truncate">
                      {request.advertising_campaign?.name || '-'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{request.city.name}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{request.request_type.name}</div>
                  </TableCell>
                  <TableCell>
                    <div className="font-mono text-sm">{request.client_phone}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm font-medium">{request.client_name}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm truncate max-w-[200px]" title={request.address}>
                      {request.address || '-'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {request.meeting_date ? formatDate(request.meeting_date) : '-'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {request.direction?.name || '-'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm truncate max-w-[150px]" title={request.problem}>
                      {request.problem || '-'}
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
                    <div className="text-sm">
                      {request.master?.full_name || '-'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm truncate max-w-[150px]" title={request.result}>
                      {request.result || '-'}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </div>
    </div>
  );
}; 