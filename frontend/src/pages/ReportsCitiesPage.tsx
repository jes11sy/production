import React, { useMemo, useCallback, useState } from 'react';
import { 
  Card, 
  CardHeader,
  CardBody,
  Button, 
  Input, 
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  Progress
} from '@heroui/react';
import { 
  BuildingOfficeIcon, 
  DocumentTextIcon, 
  BanknotesIcon,
  UserGroupIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  ChartBarIcon,
  TrophyIcon
} from '@heroicons/react/24/outline';
import { useMultipleApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { requestsApi, type Request } from '../api/requests';
import { transactionsApi } from '../api/transactions';
import { usersApi, type Master } from '../api/users';
import type { Transaction, City } from '../types/api';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

interface CityReport {
  cityId: number;
  cityName: string;
  requestsCount: number;
  requestsCompleted: number;
  requestsInProgress: number;
  totalIncome: number;
  totalExpense: number;
  netBalance: number;
  mastersCount: number;
  averageRequestValue: number;
  completionRate: number;
}

interface CityStats {
  totalCities: number;
  totalRequests: number;
  totalBalance: number;
  totalMasters: number;
  bestCity: CityReport | null;
  averageConversion: number;
}

interface CityFilters {
  search: string;
  minBalance: number;
  minConversion: number;
}

const ReportsCitiesPage: React.FC = () => {
  const { cities } = useAppData();
  
  const [filters, setFilters] = useState<CityFilters>({
    search: '',
    minBalance: 0,
    minConversion: 0
  });

  const apiCalls = useMemo(() => ({
    requests: requestsApi.getRequests,
    transactions: transactionsApi.getTransactions,
    masters: usersApi.getMasters
  }), []);

  const {
    data,
    loading,
    error
  } = useMultipleApiData<{
    requests: Request[];
    transactions: Transaction[];
    masters: Master[];
  }>(apiCalls);

  const requests = data?.requests;
  const transactions = data?.transactions;
  const masters = data?.masters;

  const reports = useMemo<CityReport[]>(() => {
    if (!requests || !transactions || !cities || !masters) return [];

    return cities.map(city => {
      const cityRequests = requests.filter(req => req.city_id === city.id);
      const cityTransactions = transactions.filter(trans => trans.city_id === city.id);
      const cityMasters = masters.filter(master => master.city_id === city.id);

      const requestsCount = cityRequests.length;
      const requestsCompleted = cityRequests.filter(req => 
        ['completed', 'done', 'finished'].includes(req.status || '')
      ).length;
      const requestsInProgress = cityRequests.filter(req => 
        ['in_progress', 'assigned', 'accepted', 'in_way', 'in_work'].includes(req.status || '')
      ).length;

      const totalIncome = cityTransactions
        .filter(trans => trans.type?.name?.toLowerCase().includes('доход') || 
                        trans.type?.name?.toLowerCase().includes('income'))
        .reduce((sum, trans) => sum + (trans.amount || 0), 0);

      const totalExpense = cityTransactions
        .filter(trans => trans.type?.name?.toLowerCase().includes('расход') || 
                        trans.type?.name?.toLowerCase().includes('expense'))
        .reduce((sum, trans) => sum + (trans.amount || 0), 0);

      const netBalance = totalIncome - totalExpense;
      const mastersCount = cityMasters.filter(m => m.status === 'active').length;
      const averageRequestValue = requestsCompleted > 0 ? totalIncome / requestsCompleted : 0;
      const completionRate = requestsCount > 0 ? (requestsCompleted / requestsCount) * 100 : 0;

      return {
        cityId: city.id,
        cityName: city.name,
        requestsCount,
        requestsCompleted,
        requestsInProgress,
        totalIncome,
        totalExpense,
        netBalance,
        mastersCount,
        averageRequestValue,
        completionRate
      };
    }).sort((a, b) => b.netBalance - a.netBalance);
  }, [requests, transactions, cities, masters]);

  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      const matchesSearch = !filters.search || 
        report.cityName.toLowerCase().includes(filters.search.toLowerCase());
      const matchesBalance = report.netBalance >= filters.minBalance;
      const matchesConversion = report.completionRate >= filters.minConversion;
      
      return matchesSearch && matchesBalance && matchesConversion;
    });
  }, [reports, filters]);

  const stats = useMemo<CityStats>(() => {
    if (filteredReports.length === 0) {
      return {
        totalCities: 0,
        totalRequests: 0,
        totalBalance: 0,
        totalMasters: 0,
        bestCity: null,
        averageConversion: 0
      };
    }

    const totalRequests = filteredReports.reduce((sum, report) => sum + report.requestsCount, 0);
    const totalBalance = filteredReports.reduce((sum, report) => sum + report.netBalance, 0);
    const totalMasters = filteredReports.reduce((sum, report) => sum + report.mastersCount, 0);
    const averageConversion = filteredReports.length > 0 
      ? filteredReports.reduce((sum, report) => sum + report.completionRate, 0) / filteredReports.length
      : 0;
    
    const bestCity = filteredReports.reduce((best, current) => 
      !best || current.netBalance > best.netBalance ? current : best
    , null as CityReport | null);

    return {
      totalCities: filteredReports.length,
      totalRequests,
      totalBalance,
      totalMasters,
      bestCity,
      averageConversion
    };
  }, [filteredReports]);

  const handleSearchChange = useCallback((value: string) => {
    setFilters(prev => ({ ...prev, search: value }));
  }, []);

  const handleBalanceChange = useCallback((value: string) => {
    setFilters(prev => ({ ...prev, minBalance: Number(value) || 0 }));
  }, []);

  const handleConversionChange = useCallback((value: string) => {
    setFilters(prev => ({ ...prev, minConversion: Number(value) || 0 }));
  }, []);

  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

  const getCompletionColor = useCallback((rate: number) => {
    if (rate >= 80) return 'success';
    if (rate >= 60) return 'warning';
    return 'danger';
  }, []);

  const exportToCSV = useCallback(() => {
    const headers = [
      'Город',
      'Заявок всего',
      'Завершено',
      'В работе',
      'Доходы',
      'Расходы',
      'Баланс',
      'Мастеров',
      'Средний чек',
      'Конверсия'
    ];

    const csvContent = [
      headers.join(','),
      ...filteredReports.map(report => [
        report.cityName,
        report.requestsCount,
        report.requestsCompleted,
        report.requestsInProgress,
        report.totalIncome,
        report.totalExpense,
        report.netBalance,
        report.mastersCount,
        report.averageRequestValue.toFixed(2),
        report.completionRate.toFixed(1)
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `отчет_по_городам_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [filteredReports]);

  const renderTableRow = useCallback((report: CityReport) => (
    <TableRow key={report.cityId}>
      <TableCell>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center rounded-full bg-blue-100 text-blue-700 p-2">
            <BuildingOfficeIcon className="h-4 w-4" />
          </div>
          <div>
            <p className="font-medium">{report.cityName}</p>
            <p className="text-sm text-gray-500">ID: {report.cityId}</p>
          </div>
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
          <div className="flex items-center justify-between">
            <span className="text-sm">Доходы:</span>
            <span className="text-sm font-bold text-green-600">
              {formatCurrency(report.totalIncome)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Расходы:</span>
            <span className="text-sm font-medium text-red-600">
              {formatCurrency(report.totalExpense)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Баланс:</span>
            <Chip 
              color={report.netBalance >= 0 ? 'success' : 'danger'} 
              size="sm" 
              variant="flat"
            >
              {formatCurrency(report.netBalance)}
            </Chip>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <UserGroupIcon className="h-4 w-4 text-gray-400" />
          <span className="text-sm font-medium">{report.mastersCount}</span>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Средний чек: {formatCurrency(report.averageRequestValue)}
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">Конверсия:</span>
            <Chip 
              color={getCompletionColor(report.completionRate)} 
              size="sm" 
              variant="flat"
            >
              {report.completionRate.toFixed(1)}%
            </Chip>
          </div>
          <Progress 
            value={report.completionRate} 
            color={getCompletionColor(report.completionRate)}
            size="sm"
            className="w-full"
          />
        </div>
      </TableCell>
    </TableRow>
  ), [formatCurrency, getCompletionColor]);

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
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center rounded-full bg-blue-100 text-blue-700 p-3">
            <BuildingOfficeIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Отчет по городам</h1>
            <p className="text-gray-600">Аналитика работы и финансов по городам</p>
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
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardBody className="text-center">
            <BuildingOfficeIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Городов</p>
            <p className="text-2xl font-bold text-blue-700">{stats.totalCities}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardBody className="text-center">
            <DocumentTextIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Заявок всего</p>
            <p className="text-2xl font-bold text-green-700">{stats.totalRequests}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardBody className="text-center">
            <BanknotesIcon className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Общий баланс</p>
            <p className="text-2xl font-bold text-purple-700">{formatCurrency(stats.totalBalance)}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardBody className="text-center">
            <UserGroupIcon className="w-8 h-8 text-orange-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Мастеров</p>
            <p className="text-2xl font-bold text-orange-700">{stats.totalMasters}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100 border-cyan-200">
          <CardBody className="text-center">
            <ChartBarIcon className="w-8 h-8 text-cyan-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Средняя конверсия</p>
            <p className="text-2xl font-bold text-cyan-700">{stats.averageConversion.toFixed(1)}%</p>
          </CardBody>
        </Card>
      </div>

      {/* Фильтры */}
      <Card className="mb-8">
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              placeholder="Поиск по названию города"
              startContent={<MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />}
              value={filters.search}
              onChange={(e) => handleSearchChange(e.target.value)}
              size="md"
            />
            <Input
              type="number"
              placeholder="Минимальный баланс (₽)"
              value={filters.minBalance.toString()}
              onChange={(e) => handleBalanceChange(e.target.value)}
              size="md"
            />
            <Input
              type="number"
              placeholder="Минимальная конверсия (%)"
              value={filters.minConversion.toString()}
              onChange={(e) => handleConversionChange(e.target.value)}
              min="0"
              max="100"
              size="md"
            />
          </div>
        </CardBody>
      </Card>

      {/* Лучший город */}
      {stats.bestCity && (
        <Card className="mb-8 bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-200">
          <CardBody>
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center rounded-full bg-yellow-500 text-white p-3">
                <TrophyIcon className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-yellow-800">Лучший город по балансу</h3>
                <p className="text-yellow-700">
                  {stats.bestCity.cityName} - баланс {formatCurrency(stats.bestCity.netBalance)}
                  ({stats.bestCity.completionRate.toFixed(1)}% конверсия)
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Таблица отчетов */}
      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold">
            Детальный отчет по городам ({filteredReports.length})
          </h3>
        </CardHeader>
        <CardBody>
          <Table aria-label="Отчет по городам">
            <TableHeader>
              <TableColumn>Город</TableColumn>
              <TableColumn>Заявки</TableColumn>
              <TableColumn>Финансы</TableColumn>
              <TableColumn>Мастера</TableColumn>
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

export default ReportsCitiesPage; 