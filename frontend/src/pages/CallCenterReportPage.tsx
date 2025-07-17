import React, { useMemo, useCallback, useState } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Button,
  Input,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  Spinner
} from '@heroui/react';
import { 
  DocumentArrowDownIcon, 
  MagnifyingGlassIcon,
  PhoneIcon,
  DocumentTextIcon,
  CalendarDaysIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { useMultipleApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { requestsApi, type Request } from '../api/requests';
import { usersApi } from '../api/users';
import type { City } from '../types/api';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

interface CallCenterFilters {
  city: string;
  dateFrom: string;
  dateTo: string;
  status: string;
  search: string;
}

interface CallCenterStats {
  totalRequests: number;
  completedRequests: number;
  pendingRequests: number;
  conversionRate: number;
}

const CallCenterReportPage: React.FC = () => {
  const { cities } = useAppData();
  
  const [filters, setFilters] = useState<CallCenterFilters>({
    city: '',
    dateFrom: '',
    dateTo: '',
    status: '',
    search: ''
  });

  const apiCalls = useMemo(() => ({
    requests: requestsApi.getRequests
  }), []);

  const {
    data,
    loading,
    error
  } = useMultipleApiData<{
    requests: Request[];
  }>(apiCalls);

  const requests = data?.requests;

  const filteredRequests = useMemo(() => {
    if (!requests) return [];

    return requests.filter(request => {
      // Фильтр по городу
      if (filters.city && request.city?.name !== filters.city) return false;
      
      // Фильтр по дате
      if (filters.dateFrom || filters.dateTo) {
        const requestDate = new Date(request.created_at || '');
        if (filters.dateFrom && requestDate < new Date(filters.dateFrom)) return false;
        if (filters.dateTo && requestDate > new Date(filters.dateTo)) return false;
      }
      
      // Фильтр по статусу
      if (filters.status && request.status !== filters.status) return false;
      
      // Фильтр по поиску
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        if (!(
          request.client_name?.toLowerCase().includes(searchTerm) ||
          request.client_phone?.includes(searchTerm) ||
          request.address?.toLowerCase().includes(searchTerm)
        )) return false;
      }
      
      return true;
    });
  }, [requests, filters]);

  const stats = useMemo<CallCenterStats>(() => {
    if (!filteredRequests.length) {
      return {
        totalRequests: 0,
        completedRequests: 0,
        pendingRequests: 0,
        conversionRate: 0
      };
    }

    const totalRequests = filteredRequests.length;
    const completedRequests = filteredRequests.filter(r => 
      ['completed', 'done', 'finished'].includes(r.status || '')
    ).length;
    const pendingRequests = filteredRequests.filter(r => 
      ['new', 'pending', 'waiting'].includes(r.status || '')
    ).length;
    const conversionRate = totalRequests > 0 ? (completedRequests / totalRequests) * 100 : 0;

    return {
      totalRequests,
      completedRequests,
      pendingRequests,
      conversionRate
    };
  }, [filteredRequests]);

  const handleFilterChange = useCallback((field: keyof CallCenterFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  }, []);

  const exportToCSV = useCallback(() => {
    const headers = [
      'Дата',
      'Клиент',
      'Телефон',
      'Город',
      'Адрес',
      'Статус',
      'Мастер'
    ];

    const csvContent = [
      headers.join(','),
      ...filteredRequests.map(request => [
        request.created_at?.split('T')[0] || '',
        request.client_name || '',
        request.client_phone || '',
        request.city?.name || '',
        request.address || '',
        request.status || '',
        request.master?.full_name || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `отчет_колл_центра_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [filteredRequests]);

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'completed':
      case 'done':
      case 'finished':
        return 'success';
      case 'in_progress':
      case 'assigned':
        return 'warning';
      case 'new':
      case 'pending':
        return 'primary';
      case 'cancelled':
        return 'danger';
      default:
        return 'default';
    }
  }, []);

  const getStatusLabel = useCallback((status: string) => {
    switch (status) {
      case 'completed':
      case 'done':
      case 'finished':
        return 'Выполнено';
      case 'in_progress':
        return 'В работе';
      case 'assigned':
        return 'Назначено';
      case 'new':
        return 'Новая';
      case 'pending':
        return 'Ожидает';
      case 'cancelled':
        return 'Отменена';
      default:
        return status || 'Неизвестно';
    }
  }, []);

  const renderRequestRow = useCallback((request: Request) => (
    <TableRow key={request.id}>
      <TableCell>
        <div>
          <p className="font-medium">{request.client_name || 'Не указано'}</p>
          <div className="flex items-center gap-2 mt-1">
            <PhoneIcon className="h-3 w-3 text-gray-400" />
            <a 
              href={`tel:${request.client_phone}`}
              className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
            >
              {request.client_phone || 'Не указано'}
            </a>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div>
          <p className="text-sm">{request.city?.name || 'Не указано'}</p>
          <p className="text-xs text-gray-500">{request.address || 'Адрес не указан'}</p>
        </div>
      </TableCell>
      <TableCell>
        <Chip
          color={getStatusColor(request.status || '')}
          size="sm"
          variant="flat"
        >
          {getStatusLabel(request.status || '')}
        </Chip>
      </TableCell>
      <TableCell>
        <div className="text-sm">
          <p>{request.master?.full_name || 'Не назначен'}</p>
          <p className="text-xs text-gray-500">
            {request.created_at?.split('T')[0] || 'Дата не указана'}
          </p>
        </div>
      </TableCell>
    </TableRow>
  ), [getStatusColor, getStatusLabel]);

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Card className="bg-red-50 border-red-200">
          <CardBody>
            <p className="text-red-700">Ошибка загрузки данных: {error}</p>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Заголовок */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center rounded-full bg-indigo-100 text-indigo-700 p-3">
            <PhoneIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Отчет колл-центра</h1>
            <p className="text-gray-600">Аналитика обращений и обработки заявок</p>
          </div>
        </div>
        <Button 
          color="primary" 
          startContent={<DocumentArrowDownIcon className="h-4 w-4" />}
          onClick={exportToCSV}
        >
          Экспорт CSV
        </Button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardBody className="text-center">
            <DocumentTextIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Всего заявок</p>
            <p className="text-2xl font-bold text-blue-700">{stats.totalRequests}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardBody className="text-center">
            <CheckCircleIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Выполнено</p>
            <p className="text-2xl font-bold text-green-700">{stats.completedRequests}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardBody className="text-center">
            <CalendarDaysIcon className="w-8 h-8 text-orange-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">В ожидании</p>
            <p className="text-2xl font-bold text-orange-700">{stats.pendingRequests}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardBody className="text-center">
            <PhoneIcon className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Конверсия</p>
            <p className="text-2xl font-bold text-purple-700">{stats.conversionRate.toFixed(1)}%</p>
          </CardBody>
        </Card>
      </div>

      {/* Фильтры */}
      <Card className="mb-8">
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <Input
              placeholder="Поиск по клиенту, телефону, адресу"
              startContent={<MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />}
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              size="md"
            />
            <select
              value={filters.city}
              onChange={(e) => handleFilterChange('city', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все города</option>
              {cities?.map(city => (
                <option key={city.id} value={city.name}>{city.name}</option>
              ))}
            </select>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все статусы</option>
              <option value="new">Новая</option>
              <option value="pending">Ожидает</option>
              <option value="assigned">Назначено</option>
              <option value="in_progress">В работе</option>
              <option value="completed">Выполнено</option>
              <option value="cancelled">Отменена</option>
            </select>
            <Input
              type="date"
              label="Дата от"
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              size="md"
            />
            <Input
              type="date"
              label="Дата до"
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              size="md"
            />
          </div>
        </CardBody>
      </Card>

      {/* Таблица заявок */}
      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold">
            Заявки колл-центра ({filteredRequests.length})
          </h3>
        </CardHeader>
        <CardBody>
          <Table aria-label="Отчет колл-центра">
            <TableHeader>
              <TableColumn>Клиент</TableColumn>
              <TableColumn>Местоположение</TableColumn>
              <TableColumn>Статус</TableColumn>
              <TableColumn>Мастер/Дата</TableColumn>
            </TableHeader>
            <TableBody>
              {filteredRequests.map(renderRequestRow)}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
};

export default CallCenterReportPage; 