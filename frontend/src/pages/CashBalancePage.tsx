import React, { useMemo, useCallback, useState } from 'react';
import { 
  Card, 
  Input, 
  Chip,
  CardBody,
  CardHeader
} from '@heroui/react';
import { 
  BanknotesIcon, 
  ArrowUpIcon, 
  ArrowDownIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { useApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { transactionsApi } from '../api/transactions';
import type { Transaction } from '../types/api';
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

interface BalanceFilters {
  search: string;
  city: string;
  type: string;
}

const CashBalancePage: React.FC = () => {
  const { cities, transactionTypes } = useAppData();
  
  const [filters, setFilters] = useState<BalanceFilters>({
    search: '',
    city: '',
    type: ''
  });

  const fetchTransactions = useCallback(() => transactionsApi.getTransactions(), []);
  const { data: transactions, loading, error } = useApiData<Transaction[]>(
    fetchTransactions
  );

  const filteredTransactions = useMemo(() => {
    if (!transactions) return [];
    
    return transactions.filter(transaction => {
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        if (!(
          transaction.description?.toLowerCase().includes(searchTerm) ||
          transaction.amount?.toString().includes(searchTerm)
        )) return false;
      }
      
      if (filters.city && transaction.city?.name !== filters.city) return false;
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
      const amount = trans.amount || 0;

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
      const amount = trans.amount || 0;

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

  const handleFilterChange = useCallback((field: keyof BalanceFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  }, []);

  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

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
          <div className="flex items-center justify-center rounded-full bg-blue-100 text-blue-700 p-3">
            <ChartBarIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Баланс кассы</h1>
            <p className="text-gray-600">Аналитика доходов и расходов</p>
          </div>
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
            <p className="text-sm text-gray-600 mb-1">Чистый баланс</p>
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
          </div>
        </CardBody>
      </Card>

      {/* Баланс по городам и типам */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <BuildingOfficeIcon className="w-6 h-6 text-gray-600" />
              Баланс по городам
            </h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {cityBalances.map(cityBalance => (
                <div key={cityBalance.cityId} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold">{cityBalance.cityName}</h4>
                    <Chip 
                      color={cityBalance.balance >= 0 ? 'success' : 'danger'}
                      variant="flat"
                      size="lg"
                    >
                      {formatCurrency(cityBalance.balance)}
                    </Chip>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-green-600 font-medium">{formatCurrency(cityBalance.income)}</div>
                      <div className="text-gray-500">Доходы</div>
                    </div>
                    <div className="text-center">
                      <div className="text-red-600 font-medium">{formatCurrency(cityBalance.expense)}</div>
                      <div className="text-gray-500">Расходы</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{cityBalance.transactionsCount}</div>
                      <div className="text-gray-500">Транзакций</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <ChartBarIcon className="w-6 h-6 text-gray-600" />
              Баланс по типам
            </h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {typeBalances.map(typeBalance => (
                <div key={typeBalance.typeId} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold">{typeBalance.typeName}</h4>
                    <Chip 
                      color={typeBalance.balance >= 0 ? 'success' : 'danger'}
                      variant="flat"
                      size="lg"
                    >
                      {formatCurrency(typeBalance.balance)}
                    </Chip>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-green-600 font-medium">{formatCurrency(typeBalance.income)}</div>
                      <div className="text-gray-500">Доходы</div>
                    </div>
                    <div className="text-center">
                      <div className="text-red-600 font-medium">{formatCurrency(typeBalance.expense)}</div>
                      <div className="text-gray-500">Расходы</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{typeBalance.transactionsCount}</div>
                      <div className="text-gray-500">Транзакций</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default CashBalancePage; 