import React, { useMemo, useCallback, useState } from 'react';
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
  CardBody,
  CardHeader
} from '@heroui/react';
import { 
  BanknotesIcon, 
  PlusIcon, 
  ArrowUpIcon, 
  ArrowDownIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { useMultipleApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { transactionsApi } from '../api/transactions';
import type { Transaction, TransactionType } from '../types/api';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

interface CashSummary {
  totalIncome: number;
  totalExpense: number;
  netBalance: number;
  transactionsCount: number;
}

interface CityBalance {
  cityId: number;
  cityName: string;
  income: number;
  expense: number;
  balance: number;
  transactionsCount: number;
}

interface TypeBalance {
  typeId: number;
  typeName: string;
  income: number;
  expense: number;
  balance: number;
  transactionsCount: number;
}

interface CashFilters {
  search: string;
  city: string;
  type: string;
  dateStart: string;
  dateEnd: string;
}

const CashRegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { cities, transactionTypes } = useAppData();
  
  const [filters, setFilters] = useState<CashFilters>({
    search: '',
    city: '',
    type: '',
    dateStart: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    dateEnd: new Date().toISOString().split('T')[0]
  });

  const apiCalls = useMemo(() => ({
    transactions: transactionsApi.getTransactions
  }), []);

  const {
    data,
    loading,
    error
  } = useMultipleApiData<{
    transactions: Transaction[];
  }>(apiCalls);

  const transactions = data?.transactions;

  const filteredTransactions = useMemo(() => {
    if (!transactions) return [];
    
    return transactions.filter(transaction => {
      // Фильтр по дате
      if (transaction.created_at) {
        const transDate = new Date(transaction.created_at);
        const startDate = new Date(filters.dateStart);
        const endDate = new Date(filters.dateEnd);
        if (!(transDate >= startDate && transDate <= endDate)) return false;
      }
      
      // Фильтр по поиску
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        if (!(
          transaction.description?.toLowerCase().includes(searchTerm) ||
          transaction.amount?.toString().includes(searchTerm)
        )) return false;
      }
      
      // Фильтр по городу
      if (filters.city && transaction.city?.name !== filters.city) return false;
      
      // Фильтр по типу
      if (filters.type && transaction.type?.name !== filters.type) return false;
      
      return true;
    });
  }, [transactions, filters]);

  const cashSummary = useMemo<CashSummary>(() => {
    if (!filteredTransactions.length) {
      return { totalIncome: 0, totalExpense: 0, netBalance: 0, transactionsCount: 0 };
    }

    let totalIncome = 0;
    let totalExpense = 0;

    filteredTransactions.forEach(trans => {
      const amount = trans.amount || 0;
      if (trans.type?.name?.toLowerCase().includes('доход') || 
          trans.type?.name?.toLowerCase().includes('income')) {
        totalIncome += amount;
      } else if (trans.type?.name?.toLowerCase().includes('расход') || 
                 trans.type?.name?.toLowerCase().includes('expense')) {
        totalExpense += amount;
      }
    });

    return {
      totalIncome,
      totalExpense,
      netBalance: totalIncome - totalExpense,
      transactionsCount: filteredTransactions.length
    };
  }, [filteredTransactions]);

  const cityBalances = useMemo<CityBalance[]>(() => {
    if (!filteredTransactions.length || !cities) return [];

    const cityMap = new Map<number, CityBalance>();

    filteredTransactions.forEach(trans => {
      const cityId = trans.city_id;
      const cityName = trans.city?.name || 'Неизвестно';
      const amount = trans.amount || 0;
      
      if (!cityMap.has(cityId)) {
        cityMap.set(cityId, {
          cityId,
          cityName,
          income: 0,
          expense: 0,
          balance: 0,
          transactionsCount: 0
        });
      }

      const cityBalance = cityMap.get(cityId)!;
      cityBalance.transactionsCount++;

      if (trans.type?.name?.toLowerCase().includes('доход') || 
          trans.type?.name?.toLowerCase().includes('income')) {
        cityBalance.income += amount;
      } else if (trans.type?.name?.toLowerCase().includes('расход') || 
                 trans.type?.name?.toLowerCase().includes('expense')) {
        cityBalance.expense += amount;
      }
      
      cityBalance.balance = cityBalance.income - cityBalance.expense;
    });

    return Array.from(cityMap.values()).sort((a, b) => b.balance - a.balance);
  }, [filteredTransactions, cities]);

  const typeBalances = useMemo<TypeBalance[]>(() => {
    if (!filteredTransactions.length || !transactionTypes) return [];

    const typeMap = new Map<number, TypeBalance>();

    filteredTransactions.forEach(trans => {
      const typeId = trans.type_id;
      const typeName = trans.type?.name || 'Неизвестно';
      const amount = trans.amount || 0;
      
      if (!typeMap.has(typeId)) {
        typeMap.set(typeId, {
          typeId,
          typeName,
          income: 0,
          expense: 0,
          balance: 0,
          transactionsCount: 0
        });
      }

      const typeBalance = typeMap.get(typeId)!;
      typeBalance.transactionsCount++;

      if (trans.type?.name?.toLowerCase().includes('доход') || 
          trans.type?.name?.toLowerCase().includes('income')) {
        typeBalance.income += amount;
      } else {
        typeBalance.expense += amount;
      }
      
      typeBalance.balance = typeBalance.income - typeBalance.expense;
    });

    return Array.from(typeMap.values()).sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance));
  }, [filteredTransactions, transactionTypes]);

  const handleFilterChange = useCallback((field: keyof CashFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  }, []);

  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

  const renderTransactionRow = useCallback((transaction: Transaction) => (
    <TableRow key={transaction.id}>
      <TableCell>
        <div>
          <p className="font-medium">{transaction.description || 'Без описания'}</p>
          <p className="text-sm text-gray-500">{transaction.created_at?.split('T')[0]}</p>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <BuildingOfficeIcon className="w-4 h-4 text-gray-400" />
          <span className="text-sm">{transaction.city?.name || 'Неизвестно'}</span>
        </div>
      </TableCell>
      <TableCell>
        <Chip
          color={transaction.type?.name?.toLowerCase().includes('доход') ? 'success' : 'danger'}
          size="sm"
          variant="flat"
        >
          {transaction.type?.name || 'Неизвестно'}
        </Chip>
      </TableCell>
      <TableCell>
        <div className={`font-bold ${
          transaction.type?.name?.toLowerCase().includes('доход') ? 'text-green-600' : 'text-red-600'
        }`}>
          {transaction.type?.name?.toLowerCase().includes('доход') ? '+' : '-'}
          {formatCurrency(transaction.amount || 0)}
        </div>
      </TableCell>
    </TableRow>
  ), [formatCurrency]);

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
          <div className="flex items-center justify-center rounded-full bg-green-100 text-green-700 p-3">
            <BanknotesIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Касса</h1>
            <p className="text-gray-600">Управление финансами и транзакциями</p>
          </div>
        </div>
        <div className="flex gap-3">
          <Button 
            color="success" 
            startContent={<ArrowUpIcon className="h-4 w-4" />}
            onClick={() => navigate('/cash-income-add')}
          >
            Доход
          </Button>
          <Button 
            color="danger" 
            startContent={<ArrowDownIcon className="h-4 w-4" />}
            onClick={() => navigate('/cash-expense-add')}
          >
            Расход
          </Button>
        </div>
      </div>

      {/* Общая статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardBody className="text-center">
            <ArrowUpIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Доходы</p>
            <p className="text-2xl font-bold text-green-700">{formatCurrency(cashSummary.totalIncome)}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardBody className="text-center">
            <ArrowDownIcon className="w-8 h-8 text-red-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Расходы</p>
            <p className="text-2xl font-bold text-red-700">{formatCurrency(cashSummary.totalExpense)}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardBody className="text-center">
            <BanknotesIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Баланс</p>
            <p className={`text-2xl font-bold ${cashSummary.netBalance >= 0 ? 'text-green-700' : 'text-red-700'}`}>
              {formatCurrency(cashSummary.netBalance)}
            </p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardBody className="text-center">
            <ChartBarIcon className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Транзакций</p>
            <p className="text-2xl font-bold text-purple-700">{cashSummary.transactionsCount}</p>
          </CardBody>
        </Card>
      </div>

      {/* Фильтры */}
      <Card className="mb-8">
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <Input
              placeholder="Поиск по описанию или сумме"
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
              value={filters.type}
              onChange={(e) => handleFilterChange('type', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все типы</option>
              {transactionTypes?.map(type => (
                <option key={type.id} value={type.name}>{type.name}</option>
              ))}
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
          </div>
        </CardBody>
      </Card>

      {/* Балансы по городам и типам */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <Card>
          <CardHeader>
            <h3 className="text-xl font-semibold">Баланс по городам</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {cityBalances.map(cityBalance => (
                <div key={cityBalance.cityId} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <BuildingOfficeIcon className="w-4 h-4 text-gray-500" />
                    <span className="font-medium">{cityBalance.cityName}</span>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${cityBalance.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(cityBalance.balance)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {cityBalance.transactionsCount} транзакций
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-xl font-semibold">Баланс по типам</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {typeBalances.map(typeBalance => (
                <div key={typeBalance.typeId} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">{typeBalance.typeName}</span>
                  <div className="text-right">
                    <div className={`font-bold ${typeBalance.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(typeBalance.balance)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {typeBalance.transactionsCount} транзакций
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Таблица транзакций */}
      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold">
            Последние транзакции ({filteredTransactions.length})
          </h3>
        </CardHeader>
        <CardBody>
          <Table aria-label="Транзакции">
            <TableHeader>
              <TableColumn>Описание</TableColumn>
              <TableColumn>Город</TableColumn>
              <TableColumn>Тип</TableColumn>
              <TableColumn>Сумма</TableColumn>
            </TableHeader>
            <TableBody>
              {filteredTransactions.slice(0, 50).map(renderTransactionRow)}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
};

export default CashRegisterPage; 