import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useApiData } from '../hooks/useApiData';
import { requestsApi, type Request } from '../api/requests';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

interface StatsCardProps {
  title: string;
  count: number;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, count, color = 'primary' }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium text-gray-700">{title}</h3>
    <p className={`text-2xl font-bold ${
      color === 'primary' ? 'text-blue-600' :
      color === 'success' ? 'text-green-600' :
      color === 'warning' ? 'text-yellow-600' :
      color === 'danger' ? 'text-red-600' : 'text-gray-600'
    }`}>{count}</p>
  </div>
);

const IncomingRequestsPage: React.FC = () => {
  const { data: requests, loading, error, refetch } = useApiData<Request[]>(
    async () => await requestsApi.getRequests(),
    {
      errorMessage: 'Ошибка загрузки входящих заявок'
    }
  );

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Фильтрация входящих заявок
  const allowedStatuses = ['Новая', 'Перезвонить', 'ТНО', 'Отказ'];
  const filteredRequests = useMemo(() => {
    if (!requests) return [];
    return requests.filter(r => allowedStatuses.includes(r.status));
  }, [requests]);

  // Статистика по статусам
  const stats = useMemo(() => {
    const total = filteredRequests.length;
    const newRequests = filteredRequests.filter(r => r.status === 'Новая').length;
    const callbacks = filteredRequests.filter(r => r.status === 'Перезвонить').length;
    const refused = filteredRequests.filter(r => r.status === 'Отказ').length;

    return { total, newRequests, callbacks, refused };
  }, [filteredRequests]);

  // Вспомогательные функции
  const getStatusBadge = useCallback((status: string) => {
    const statusConfig = {
      'Новая': { label: 'Новая', color: 'bg-blue-100 text-blue-800' },
      'Перезвонить': { label: 'Перезвон', color: 'bg-yellow-100 text-yellow-800' },
      'ТНО': { label: 'ТНО', color: 'bg-gray-100 text-gray-800' },
      'Отказ': { label: 'Отказ', color: 'bg-red-100 text-red-800' }
    };
    const config = statusConfig[status as keyof typeof statusConfig] || { 
      label: status, 
      color: 'bg-gray-100 text-gray-800'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  }, []);

  const formatDate = useCallback((dateString: string | undefined) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleString('ru-RU');
    } catch {
      return dateString;
    }
  }, []);

  if (!mounted) {
    return <LoadingSkeleton />;
  }

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Ошибка загрузки данных: {error}</p>
        <button 
          onClick={refetch}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Повторить
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Входящие заявки</h1>
      
      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatsCard title="Всего входящих" count={stats.total} color="primary" />
        <StatsCard title="Новые" count={stats.newRequests} color="success" />
        <StatsCard title="Перезвон" count={stats.callbacks} color="warning" />
        <StatsCard title="Отказы" count={stats.refused} color="danger" />
      </div>

      {/* Таблица */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Список входящих заявок</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">РК</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Город</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Тип заявки</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Телефон</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Имя</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Адрес</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Дата встречи</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Направление</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Проблема</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Статус</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">АТС</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">КЦ</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Заметка КЦ</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRequests.length === 0 ? (
                <tr>
                  <td colSpan={14} className="px-6 py-8 text-center text-gray-500">
                    Входящие заявки не найдены
                  </td>
                </tr>
              ) : (
                filteredRequests.map((request) => (
                  <tr key={request.id} className="hover:bg-gray-50">
                    <td className="px-3 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {request.id}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.advertising_campaign?.name || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.city?.name || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.request_type?.name || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.client_phone || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.client_name || '-'}
                    </td>
                    <td className="px-3 py-4 text-sm text-gray-700 max-w-xs truncate">
                      {request.address || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {formatDate(request.meeting_date)}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.direction?.name || '-'}
                    </td>
                    <td className="px-3 py-4 text-sm text-gray-700 max-w-xs truncate">
                      {request.problem || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm">
                      {getStatusBadge(request.status)}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.ats_number || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-700">
                      {request.call_center_name || '-'}
                    </td>
                    <td className="px-3 py-4 text-sm text-gray-700 max-w-xs truncate">
                      {request.call_center_notes || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default IncomingRequestsPage; 