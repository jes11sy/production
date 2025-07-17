import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Select,
  SelectItem
} from '@heroui/react';
import { 
  ArrowUpIcon, 
  PlusIcon, 
  BuildingOfficeIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  CalendarIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { useApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { useNotification } from '../contexts/NotificationContext';
import { transactionsApi } from '../api/transactions';
import type { Transaction } from '../types/api';

interface IncomeFilters {
  search: string;
  cityId: string;
  typeId: string;
  startDate: string;
  endDate: string;
}

interface CityIncome {
  cityName: string;
  total: number;
  count: number;
  average: number;
}

interface TypeIncome {
  typeName: string;
  total: number;
  count: number;
  average: number;
}

interface IncomeStats {
  totalIncome: number;
  totalTransactions: number;
  citiesCount: number;
  typesCount: number;
  averagePerTransaction: number;
}

const CashIncomePage: React.FC = () => {
  const navigate = useNavigate();
  const { cities, transactionTypes } = useAppData();
  const { showError } = useNotification();

  // API Data
  const { 
    data: transactions, 
    loading, 
    error, 
    refetch 
  } = useApiData(
    useCallback(() => transactionsApi.getTransactions(), [])
  );

  // Local state
  const [filters, setFilters] = useState<IncomeFilters>({
    search: '',
    cityId: '',
    typeId: '',
    startDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0]
  });

  // Memoized filter handlers
  const handleFilterChange = useCallback((key: keyof IncomeFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFilterChange('search', e.target.value);
  }, [handleFilterChange]);

  const handleCityChange = useCallback((keys: any) => {
    const value = Array.from(keys)[0] as string || '';
    handleFilterChange('cityId', value);
  }, [handleFilterChange]);

  const handleTypeChange = useCallback((keys: any) => {
    const value = Array.from(keys)[0] as string || '';
    handleFilterChange('typeId', value);
  }, [handleFilterChange]);

  const handleStartDateChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFilterChange('startDate', e.target.value);
  }, [handleFilterChange]);

  const handleEndDateChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFilterChange('endDate', e.target.value);
  }, [handleFilterChange]);

  // Memoized income transactions filtering
  const incomeTransactions = useMemo(() => {
    if (!transactions) return [];
    return transactions.filter(transaction => {
      return transaction.amount > 0; // Только положительные суммы
    });
  }, [transactions]);

  // Memoized filtered transactions
  const filteredTransactions = useMemo(() => {
    if (!incomeTransactions.length) return [];

    return incomeTransactions.filter(transaction => {
             // Search filter
       const matchesSearch = !filters.search || 
         transaction.id.toString().includes(filters.search) ||
         transaction.amount.toString().includes(filters.search) ||
         transaction.description?.toLowerCase().includes(filters.search.toLowerCase());
       
       // City filter
       const matchesCity = !filters.cityId || transaction.city?.id.toString() === filters.cityId;
       
       // Type filter
       const matchesType = !filters.typeId || transaction.type?.id.toString() === filters.typeId;
       
       // Date filter - используем created_at или updated_at
       const transactionDate = new Date(transaction.created_at);
       const startDate = new Date(filters.startDate);
       const endDate = new Date(filters.endDate);
       const matchesDate = transactionDate >= startDate && transactionDate <= endDate;

      return matchesSearch && matchesCity && matchesType && matchesDate;
    });
  }, [incomeTransactions, filters]);

  // Memoized statistics
  const stats = useMemo((): IncomeStats => {
    if (!filteredTransactions.length) {
      return {
        totalIncome: 0,
        totalTransactions: 0,
        citiesCount: 0,
        typesCount: 0,
        averagePerTransaction: 0
      };
    }

    const totalIncome = filteredTransactions.reduce((sum, transaction) => {
      return sum + transaction.amount;
    }, 0);

    const uniqueCities = new Set(filteredTransactions.map(t => t.city?.id).filter(Boolean));
         const uniqueTypes = new Set(filteredTransactions.map(t => t.type?.id).filter(Boolean));

    return {
      totalIncome,
      totalTransactions: filteredTransactions.length,
      citiesCount: uniqueCities.size,
      typesCount: uniqueTypes.size,
      averagePerTransaction: totalIncome / filteredTransactions.length
    };
  }, [filteredTransactions]);

  // Memoized city income analytics
  const cityIncomes = useMemo((): Record<number, CityIncome> => {
    if (!filteredTransactions.length) return {};

    return filteredTransactions.reduce((acc, transaction) => {
      const city = transaction.city;
      if (!city) return acc;

      const cityId = city.id;
      const cityName = city.name;
      const amount = transaction.amount;

      if (!acc[cityId]) {
        acc[cityId] = { cityName, total: 0, count: 0, average: 0 };
      }
      acc[cityId].total += amount;
      acc[cityId].count++;
      acc[cityId].average = acc[cityId].total / acc[cityId].count;
      return acc;
    }, {} as Record<number, CityIncome>);
  }, [filteredTransactions]);

  // Memoized type income analytics
  const typeIncomes = useMemo((): Record<number, TypeIncome> => {
    if (!filteredTransactions.length) return {};

         return filteredTransactions.reduce((acc, transaction) => {
       const transactionType = transaction.type;
       if (!transactionType) return acc;

       const typeId = transactionType.id;
       const typeName = transactionType.name;
       const amount = transaction.amount;

       if (!acc[typeId]) {
         acc[typeId] = { typeName, total: 0, count: 0, average: 0 };
       }
       acc[typeId].total += amount;
       acc[typeId].count++;
       acc[typeId].average = acc[typeId].total / acc[typeId].count;
       return acc;
     }, {} as Record<number, TypeIncome>);
  }, [filteredTransactions]);

  // Memoized currency formatter
  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

  // Memoized table row renderer
  const renderTableRow = useCallback((transaction: Transaction) => {
    return (
      <TableRow key={transaction.id}>
        <TableCell>
          <span className="font-medium text-blue-600">#{transaction.id}</span>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <BuildingOfficeIcon className="h-4 w-4 text-gray-400" />
            <span>{transaction.city?.name || 'Не указан'}</span>
          </div>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <TagIcon className="h-4 w-4 text-gray-400" />
            <span>{transaction.type?.name || 'Не указан'}</span>
          </div>
        </TableCell>
        <TableCell>
          <Chip color="success" variant="flat" size="sm">
            {formatCurrency(transaction.amount)}
          </Chip>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <CalendarIcon className="h-4 w-4 text-gray-400" />
            <span>{new Date(transaction.created_at).toLocaleDateString('ru-RU')}</span>
          </div>
        </TableCell>
        <TableCell>
          {transaction.description ? (
            <span className="text-gray-600 text-sm truncate max-w-32 block" title={transaction.description}>
              {transaction.description}
            </span>
          ) : (
            <span className="text-gray-400 text-sm">Без описания</span>
          )}
        </TableCell>
      </TableRow>
    );
  }, [formatCurrency]);

  // Handle error notification
  React.useEffect(() => {
    if (error) {
      showError('Ошибка загрузки данных о транзакциях');
    }
  }, [error, showError]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center rounded-full bg-green-100 text-green-700 p-3">
            <ArrowUpIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Доходы кассы</h1>
            <p className="text-gray-600">Управление доходными транзакциями</p>
          </div>
        </div>
        <Button 
          color="success" 
          size="lg" 
          startContent={<PlusIcon className="h-5 w-5" />}
          onClick={() => navigate('/cash/income/add')}
        >
          Новый доход
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Input
            placeholder="Поиск по ID, сумме или заметкам"
            startContent={<MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />}
            value={filters.search}
            onChange={handleSearchChange}
            size="md"
            variant="bordered"
          />
          
          <Select
            placeholder="Выберите город"
            selectedKeys={filters.cityId ? [filters.cityId] : []}
            onSelectionChange={handleCityChange}
            variant="bordered"
            startContent={<BuildingOfficeIcon className="h-4 w-4 text-gray-400" />}
          >
            {cities.map(city => (
              <SelectItem key={city.id.toString()}>
                {city.name}
              </SelectItem>
            ))}
          </Select>

          <Select
            placeholder="Выберите тип"
            selectedKeys={filters.typeId ? [filters.typeId] : []}
            onSelectionChange={handleTypeChange}
            variant="bordered"
            startContent={<TagIcon className="h-4 w-4 text-gray-400" />}
          >
            {transactionTypes.map(type => (
              <SelectItem key={type.id.toString()}>
                {type.name}
              </SelectItem>
            ))}
          </Select>

          <div className="flex gap-2">
            <Input
              type="date"
              value={filters.startDate}
              onChange={handleStartDateChange}
              variant="bordered"
              size="md"
            />
            <Input
              type="date"
              value={filters.endDate}
              onChange={handleEndDateChange}
              variant="bordered"
              size="md"
            />
          </div>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <Card className="bg-gradient-to-r from-green-50 to-green-100 border-green-200 p-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center rounded-full bg-green-500 text-white p-3">
              <ArrowUpIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Общие доходы</p>
              <p className="text-2xl font-bold text-green-700">{formatCurrency(stats.totalIncome)}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-r from-blue-50 to-blue-100 border-blue-200 p-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center rounded-full bg-blue-500 text-white p-3">
              <ChartBarIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Транзакций</p>
              <p className="text-2xl font-bold text-blue-700">{stats.totalTransactions}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-r from-purple-50 to-purple-100 border-purple-200 p-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center rounded-full bg-purple-500 text-white p-3">
              <BuildingOfficeIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Городов</p>
              <p className="text-2xl font-bold text-purple-700">{stats.citiesCount}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-r from-orange-50 to-orange-100 border-orange-200 p-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center rounded-full bg-orange-500 text-white p-3">
              <TagIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Типов</p>
              <p className="text-2xl font-bold text-orange-700">{stats.typesCount}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-r from-indigo-50 to-indigo-100 border-indigo-200 p-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center rounded-full bg-indigo-500 text-white p-3">
              <ChartBarIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Среднее</p>
              <p className="text-2xl font-bold text-indigo-700">
                {formatCurrency(stats.averagePerTransaction || 0)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* City Income Analytics */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <BuildingOfficeIcon className="h-6 w-6 text-gray-600" />
            <h3 className="text-xl font-semibold">Доходы по городам</h3>
          </div>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {Object.entries(cityIncomes)
              .sort(([,a], [,b]) => b.total - a.total)
              .map(([cityId, data]) => (
                <div key={cityId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{data.cityName}</span>
                      <Chip color="success" variant="flat" size="sm">
                        {formatCurrency(data.total)}
                      </Chip>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>Транзакций: {data.count}</span>
                      <span>Среднее: {formatCurrency(data.average)}</span>
                    </div>
                  </div>
                </div>
              ))}
            {Object.keys(cityIncomes).length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <BuildingOfficeIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>Нет данных для отображения</p>
              </div>
            )}
          </div>
        </Card>

        {/* Type Income Analytics */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <TagIcon className="h-6 w-6 text-gray-600" />
            <h3 className="text-xl font-semibold">Доходы по типам</h3>
          </div>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {Object.entries(typeIncomes)
              .sort(([,a], [,b]) => b.total - a.total)
              .map(([typeId, data]) => (
                <div key={typeId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{data.typeName}</span>
                      <Chip color="success" variant="flat" size="sm">
                        {formatCurrency(data.total)}
                      </Chip>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>Транзакций: {data.count}</span>
                      <span>Среднее: {formatCurrency(data.average)}</span>
                    </div>
                  </div>
                </div>
              ))}
            {Object.keys(typeIncomes).length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <TagIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>Нет данных для отображения</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Transactions Table */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold">Доходные транзакции ({filteredTransactions.length})</h3>
          <Button 
            variant="light" 
            color="primary"
            onClick={() => navigate('/transactions')}
          >
            Все транзакции
          </Button>
        </div>
        
        <Table 
          aria-label="Доходные транзакции"
          classNames={{
            wrapper: "min-h-[400px]",
          }}
        >
          <TableHeader>
            <TableColumn>ID</TableColumn>
            <TableColumn>ГОРОД</TableColumn>
            <TableColumn>ТИП</TableColumn>
            <TableColumn>СУММА</TableColumn>
            <TableColumn>ДАТА</TableColumn>
            <TableColumn>ЗАМЕТКИ</TableColumn>
          </TableHeader>
          <TableBody emptyContent="Нет доходных транзакций для отображения">
            {filteredTransactions.map(renderTableRow)}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
};

export default CashIncomePage; 