import React, { useMemo, useCallback, useState } from 'react';
import { 
  Card, 
  Button, 
  Input, 
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  Progress,
  Avatar,
  CardBody,
  CardHeader
} from '@heroui/react';
import { 
  UserGroupIcon, 
  DocumentTextIcon, 
  BanknotesIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  PhoneIcon,
  TrophyIcon,
  ClockIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline';
import { useMultipleApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { requestsApi, type Request } from '../api/requests';
import { usersApi, type Master } from '../api/users';
import type { City } from '../types/api';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

interface MasterReport {
  masterId: number;
  masterName: string;
  cityName: string;
  phoneNumber: string;
  status: string;
  requestsCount: number;
  requestsCompleted: number;
  requestsInProgress: number;
  requestsWaiting: number;
  totalEarnings: number;
  averageEarnings: number;
  completionRate: number;
  lastActivity: string;
  daysActive: number;
}

interface MasterStats {
  totalMasters: number;
  activeMasters: number;
  totalRequests: number;
  totalEarnings: number;
  averageConversion: number;
  topMaster: MasterReport | null;
}

interface MasterFilters {
  search: string;
  city: string;
  status: string;
  dateStart: string;
  dateEnd: string;
  minConversion: number;
}

const ReportsMastersPage: React.FC = () => {
  const { cities } = useAppData();
  
  const [filters, setFilters] = useState<MasterFilters>({
    search: '',
    city: '',
    status: '',
    dateStart: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    dateEnd: new Date().toISOString().split('T')[0],
    minConversion: 0
  });

  const apiCalls = useMemo(() => ({
    masters: usersApi.getMasters,
    requests: requestsApi.getRequests
  }), []);

  const {
    data,
    loading,
    error
  } = useMultipleApiData<{
    masters: Master[];
    requests: Request[];
  }>(apiCalls);

  const masters = data?.masters;
  const requests = data?.requests;

  const filteredRequests = useMemo(() => {
    if (!requests) return [];
    return requests.filter(req => {
      if (!req.created_at) return false;
      const reqDate = new Date(req.created_at);
      const startDate = new Date(filters.dateStart);
      const endDate = new Date(filters.dateEnd);
      return reqDate >= startDate && reqDate <= endDate;
    });
  }, [requests, filters.dateStart, filters.dateEnd]);

  const reports = useMemo<MasterReport[]>(() => {
    if (!masters || !filteredRequests || !cities) return [];

    return masters.map(master => {
      const masterRequests = filteredRequests.filter(req => req.master_id === master.id);
      const city = cities.find(c => c.id === master.city_id);

      const requestsCount = masterRequests.length;
      const requestsCompleted = masterRequests.filter(req => 
        ['completed', 'done', 'finished'].includes(req.status || '')
      ).length;
      const requestsInProgress = masterRequests.filter(req => 
        ['in_progress', 'assigned', 'accepted', 'in_way', 'in_work'].includes(req.status || '')
      ).length;
      const requestsWaiting = masterRequests.filter(req => 
        ['new', 'pending', 'waiting'].includes(req.status || '')
      ).length;

      // Примерный расчет заработка (можно улучшить при наличии данных о заработке)
      const totalEarnings = requestsCompleted * 1000; // Средняя стоимость услуги
      const averageEarnings = requestsCompleted > 0 ? totalEarnings / requestsCompleted : 0;
      const completionRate = requestsCount > 0 ? (requestsCompleted / requestsCount) * 100 : 0;

      // Последняя активность
      const lastRequest = masterRequests
        .sort((a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime())[0];
      const lastActivity = lastRequest?.created_at || master.created_at || '';
      const daysActive = lastActivity ? Math.floor((new Date().getTime() - new Date(lastActivity).getTime()) / (1000 * 60 * 60 * 24)) : 0;

      return {
        masterId: master.id,
        masterName: master.full_name,
        cityName: city?.name || 'Неизвестно',
        phoneNumber: master.phone_number || '',
        status: master.status || 'inactive',
        requestsCount,
        requestsCompleted,
        requestsInProgress,
        requestsWaiting,
        totalEarnings,
        averageEarnings,
        completionRate,
        lastActivity,
        daysActive
      };
    }).sort((a, b) => b.completionRate - a.completionRate);
  }, [masters, filteredRequests, cities]);

  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      const matchesSearch = !filters.search || 
        report.masterName.toLowerCase().includes(filters.search.toLowerCase()) ||
        report.phoneNumber.includes(filters.search) ||
        report.cityName.toLowerCase().includes(filters.search.toLowerCase());
      const matchesCity = !filters.city || report.cityName === filters.city;
      const matchesStatus = !filters.status || report.status === filters.status;
      const matchesConversion = report.completionRate >= filters.minConversion;
      
      return matchesSearch && matchesCity && matchesStatus && matchesConversion;
    });
  }, [reports, filters]);

  const stats = useMemo<MasterStats>(() => {
    if (filteredReports.length === 0) {
      return {
        totalMasters: 0,
        activeMasters: 0,
        totalRequests: 0,
        totalEarnings: 0,
        averageConversion: 0,
        topMaster: null
      };
    }

    const activeMasters = filteredReports.filter(r => r.status === 'active').length;
    const totalRequests = filteredReports.reduce((sum, r) => sum + r.requestsCount, 0);
    const totalEarnings = filteredReports.reduce((sum, r) => sum + r.totalEarnings, 0);
    const averageConversion = filteredReports.length > 0 
      ? filteredReports.reduce((sum, r) => sum + r.completionRate, 0) / filteredReports.length
      : 0;
    
    const topMaster = filteredReports.reduce((top, current) => 
      !top || current.completionRate > top.completionRate ? current : top
    , null as MasterReport | null);

    return {
      totalMasters: filteredReports.length,
      activeMasters,
      totalRequests,
      totalEarnings,
      averageConversion,
      topMaster
    };
  }, [filteredReports]);

  const handleFilterChange = useCallback((field: keyof MasterFilters, value: string | number) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  }, []);

  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'danger';
      case 'busy': return 'warning';
      default: return 'default';
    }
  }, []);

  const getStatusLabel = useCallback((status: string) => {
    switch (status) {
      case 'active': return 'Активен';
      case 'inactive': return 'Неактивен';
      case 'busy': return 'Занят';
      default: return status;
    }
  }, []);

  const exportToCSV = useCallback(() => {
    const headers = [
      'Мастер',
      'Город',
      'Телефон',
      'Статус',
      'Заявок всего',
      'Завершено',
      'В работе',
      'Ожидает',
      'Общий заработок',
      'Средний заработок',
      'Процент завершения',
      'Дней неактивности'
    ];

    const csvContent = [
      headers.join(','),
      ...filteredReports.map(report => [
        report.masterName,
        report.cityName,
        report.phoneNumber,
        getStatusLabel(report.status),
        report.requestsCount,
        report.requestsCompleted,
        report.requestsInProgress,
        report.requestsWaiting,
        report.totalEarnings,
        report.averageEarnings.toFixed(2),
        report.completionRate.toFixed(1),
        report.daysActive
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `отчет_по_мастерам_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [filteredReports, getStatusLabel]);

  const renderTableRow = useCallback((report: MasterReport) => (
    <TableRow key={report.masterId}>
      <TableCell>
        <div className="flex items-center gap-3">
          <Avatar 
            name={report.masterName}
            size="sm"
            color={getStatusColor(report.status)}
          />
          <div>
            <p className="font-medium">{report.masterName}</p>
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <BuildingOfficeIcon className="w-3 h-3" />
              {report.cityName}
            </p>
            {report.phoneNumber && (
              <div className="flex items-center gap-1 mt-1">
                <PhoneIcon className="h-3 w-3 text-gray-400" />
                <a 
                  href={`tel:${report.phoneNumber}`}
                  className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
                >
                  {report.phoneNumber}
                </a>
              </div>
            )}
          </div>
        </div>
      </TableCell>
      <TableCell>
        <Chip 
          color={getStatusColor(report.status)} 
          size="sm" 
          variant="flat"
        >
          {getStatusLabel(report.status)}
        </Chip>
        <div className="text-xs text-gray-500 mt-1 flex items-center gap-1">
          <ClockIcon className="w-3 h-3" />
          {report.daysActive} дней назад
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-sm">Всего:</span>
            <span className="text-sm font-bold">{report.requestsCount}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Завершено:</span>
            <Chip color="success" size="sm" variant="flat">
              {report.requestsCompleted}
            </Chip>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">В работе:</span>
            <Chip color="warning" size="sm" variant="flat">
              {report.requestsInProgress}
            </Chip>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-2">
          <div className="text-sm font-medium text-green-600">
            {formatCurrency(report.totalEarnings)}
          </div>
          <div className="text-xs text-gray-500">
            Средний: {formatCurrency(report.averageEarnings)}
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">Конверсия:</span>
            <Chip 
              color={report.completionRate >= 80 ? 'success' : report.completionRate >= 60 ? 'warning' : 'danger'} 
              size="sm" 
              variant="flat"
            >
              {report.completionRate.toFixed(1)}%
            </Chip>
          </div>
          <Progress 
            value={report.completionRate} 
            color={report.completionRate >= 80 ? 'success' : report.completionRate >= 60 ? 'warning' : 'danger'}
            size="sm"
            className="w-full"
          />
        </div>
      </TableCell>
    </TableRow>
  ), [getStatusColor, getStatusLabel, formatCurrency]);

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
          <div className="flex items-center justify-center rounded-full bg-purple-100 text-purple-700 p-3">
            <UserGroupIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Отчет по мастерам</h1>
            <p className="text-gray-600">Аналитика работы мастеров и их эффективности</p>
          </div>
        </div>
        <Button 
          color="primary" 
          size="lg" 
          startContent={<ArrowDownTrayIcon className="h-5 w-5" />}
          onClick={exportToCSV}
        >
          Экспорт CSV
        </Button>
      </div>

      {/* Статистические карточки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardBody className="text-center">
            <UserGroupIcon className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Мастеров всего</p>
            <p className="text-2xl font-bold text-purple-700">{stats.totalMasters}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardBody className="text-center">
            <CheckCircleIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Активных</p>
            <p className="text-2xl font-bold text-green-700">{stats.activeMasters}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardBody className="text-center">
            <DocumentTextIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Заявок</p>
            <p className="text-2xl font-bold text-blue-700">{stats.totalRequests}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardBody className="text-center">
            <BanknotesIcon className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Заработок</p>
            <p className="text-2xl font-bold text-yellow-700">{formatCurrency(stats.totalEarnings)}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100 border-cyan-200">
          <CardBody className="text-center">
            <TrophyIcon className="w-8 h-8 text-cyan-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Средняя конверсия</p>
            <p className="text-2xl font-bold text-cyan-700">{stats.averageConversion.toFixed(1)}%</p>
          </CardBody>
        </Card>
      </div>

      {/* Фильтры */}
      <Card className="mb-8">
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            <Input
              placeholder="Поиск по имени, телефону, городу"
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
              <option value="active">Активен</option>
              <option value="inactive">Неактивен</option>
              <option value="busy">Занят</option>
            </select>
            <Input
              type="date"
              label="Дата от"
              value={filters.dateStart}
              onChange={(e) => handleFilterChange('dateStart', e.target.value)}
              size="md"
            />
            <Input
              type="date"
              label="Дата до"
              value={filters.dateEnd}
              onChange={(e) => handleFilterChange('dateEnd', e.target.value)}
              size="md"
            />
            <Input
              type="number"
              placeholder="Мин. конверсия (%)"
              value={filters.minConversion.toString()}
              onChange={(e) => handleFilterChange('minConversion', Number(e.target.value) || 0)}
              min="0"
              max="100"
              size="md"
            />
          </div>
        </CardBody>
      </Card>

      {/* Лучший мастер */}
      {stats.topMaster && (
        <Card className="mb-8 bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-200">
          <CardBody>
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center rounded-full bg-yellow-500 text-white p-3">
                <TrophyIcon className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-yellow-800">Лучший мастер</h3>
                <p className="text-yellow-700">
                  {stats.topMaster.masterName} из {stats.topMaster.cityName} - 
                  конверсия {stats.topMaster.completionRate.toFixed(1)}%
                  ({stats.topMaster.requestsCompleted} из {stats.topMaster.requestsCount} заявок)
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Таблица мастеров */}
      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold">
            Детальный отчет по мастерам ({filteredReports.length})
          </h3>
        </CardHeader>
        <CardBody>
          <Table aria-label="Отчет по мастерам">
            <TableHeader>
              <TableColumn>Мастер</TableColumn>
              <TableColumn>Статус</TableColumn>
              <TableColumn>Заявки</TableColumn>
              <TableColumn>Заработок</TableColumn>
              <TableColumn>Эффективность</TableColumn>
            </TableHeader>
            <TableBody>
              {filteredReports.map(renderTableRow)}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
};

export default ReportsMastersPage; 