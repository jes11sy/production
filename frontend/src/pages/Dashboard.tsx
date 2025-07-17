import React, { useMemo, useCallback } from 'react';
import { Card, CardBody } from '@heroui/react';
import { 
  DocumentTextIcon, 
  CheckCircleIcon, 
  ClockIcon,
  UserGroupIcon,
  BanknotesIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline';
import { useApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { requestsApi, type Request } from '../api/requests';
import { transactionsApi } from '../api/transactions';
import type { Transaction } from '../types/api';
import { usersApi, type Master } from '../api/users';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

interface DashboardStats {
  todayRequests: number;
  completedRequests: number;
  inProgressRequests: number;
  totalRequests: number;
  newRequests: number;
  totalIncome: number;
  totalMasters: number;
  activeCities: number;
}

export default function Dashboard() {
  const { cities } = useAppData();
  
  const fetchRequests = useCallback(() => requestsApi.getRequests(), []);
  const fetchTransactions = useCallback(() => transactionsApi.getTransactions(), []);
  const fetchMasters = useCallback(() => usersApi.getMasters(), []);
  
  const { data: requests, loading: requestsLoading } = useApiData<Request[]>(
    fetchRequests
  );

  const { data: transactions, loading: transactionsLoading } = useApiData<Transaction[]>(
    fetchTransactions
  );

  const { data: masters, loading: mastersLoading } = useApiData<Master[]>(
    fetchMasters
  );

  const stats = useMemo<DashboardStats>(() => {
    if (!requests || !transactions || !masters) {
      return {
        todayRequests: 0,
        completedRequests: 0,
        inProgressRequests: 0,
        totalRequests: 0,
        newRequests: 0,
        totalIncome: 0,
        totalMasters: 0,
        activeCities: 0
      };
    }

    const today = new Date().toISOString().split('T')[0];
    const todayRequests = requests.filter(r => 
      r.created_at?.startsWith(today)
    ).length;

    const completedRequests = requests.filter(r => 
      r.status === 'completed'
    ).length;

    const inProgressRequests = requests.filter(r => 
      ['in_progress', 'assigned'].includes(r.status || '')
    ).length;

    const newRequests = requests.filter(r => 
      r.status === 'new'
    ).length;

    const totalIncome = transactions
      .filter(t => t.type?.name?.toLowerCase().includes('доход') || t.type?.name?.toLowerCase().includes('income'))
      .reduce((sum, t) => sum + (t.amount || 0), 0);

    const activeMasters = masters.filter(m => 
      m.status === 'active'
    ).length;

    const activeCities = cities?.length || 0;

    return {
      todayRequests,
      completedRequests,
      inProgressRequests,
      totalRequests: requests.length,
      newRequests,
      totalIncome,
      totalMasters: activeMasters,
      activeCities
    };
  }, [requests, transactions, masters, cities]);

  const isLoading = requestsLoading || transactionsLoading || mastersLoading;

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="max-w-7xl mx-auto mt-8">
      <h2 className="text-3xl font-bold mb-8">Дашборд</h2>
      
      {/* Статистика заявок */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 shadow-md">
          <CardBody className="text-center">
            <DocumentTextIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <div className="text-lg mb-1 text-gray-700">Заявок сегодня</div>
            <div className="text-3xl font-bold text-blue-600">
              {stats.todayRequests}
            </div>
          </CardBody>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-green-100 shadow-md">
          <CardBody className="text-center">
            <CheckCircleIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <div className="text-lg mb-1 text-gray-700">Завершено</div>
            <div className="text-3xl font-bold text-green-600">
              {stats.completedRequests}
            </div>
          </CardBody>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 shadow-md">
          <CardBody className="text-center">
            <ClockIcon className="w-8 h-8 text-orange-600 mx-auto mb-2" />
            <div className="text-lg mb-1 text-gray-700">В работе</div>
            <div className="text-3xl font-bold text-orange-600">
              {stats.inProgressRequests}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Общая статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-white shadow-md">
          <CardBody className="text-center p-6">
            <DocumentTextIcon className="w-10 h-10 text-blue-600 mx-auto mb-3" />
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {stats.totalRequests}
            </div>
            <div className="text-sm text-gray-600">Всего заявок</div>
          </CardBody>
        </Card>
        
        <Card className="bg-white shadow-md">
          <CardBody className="text-center p-6">
            <ClockIcon className="w-10 h-10 text-yellow-600 mx-auto mb-3" />
            <div className="text-2xl font-bold text-yellow-600 mb-1">
              {stats.newRequests}
            </div>
            <div className="text-sm text-gray-600">Новых заявок</div>
          </CardBody>
        </Card>
        
        <Card className="bg-white shadow-md">
          <CardBody className="text-center p-6">
            <BanknotesIcon className="w-10 h-10 text-green-600 mx-auto mb-3" />
            <div className="text-2xl font-bold text-green-600 mb-1">
              {stats.totalIncome.toLocaleString()} ₽
            </div>
            <div className="text-sm text-gray-600">Общий доход</div>
          </CardBody>
        </Card>
        
        <Card className="bg-white shadow-md">
          <CardBody className="text-center p-6">
            <UserGroupIcon className="w-10 h-10 text-purple-600 mx-auto mb-3" />
            <div className="text-2xl font-bold text-purple-600 mb-1">
              {stats.totalMasters}
            </div>
            <div className="text-sm text-gray-600">Активных мастеров</div>
          </CardBody>
        </Card>
      </div>

      {/* Дополнительная информация */}
      <Card className="bg-white shadow-md">
        <CardBody className="p-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <BuildingOfficeIcon className="w-6 h-6 mr-2 text-gray-600" />
            Активность по городам
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600 mb-1">
                {stats.activeCities}
              </div>
              <div className="text-sm text-gray-600">Активных городов</div>
            </div>
            <div className="text-center p-4 bg-indigo-50 rounded-lg">
              <div className="text-2xl font-bold text-indigo-600 mb-1">
                {stats.totalRequests > 0 ? Math.round((stats.completedRequests / stats.totalRequests) * 100) : 0}%
              </div>
              <div className="text-sm text-gray-600">Процент завершения</div>
            </div>
            <div className="text-center p-4 bg-cyan-50 rounded-lg">
              <div className="text-2xl font-bold text-cyan-600 mb-1">
                {stats.totalMasters > 0 ? Math.round(stats.totalRequests / stats.totalMasters) : 0}
              </div>
              <div className="text-sm text-gray-600">Заявок на мастера</div>
            </div>
            <div className="text-center p-4 bg-rose-50 rounded-lg">
              <div className="text-2xl font-bold text-rose-600 mb-1">
                {stats.totalRequests > 0 ? Math.round(stats.totalIncome / stats.totalRequests) : 0} ₽
              </div>
              <div className="text-sm text-gray-600">Средний доход</div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
} 