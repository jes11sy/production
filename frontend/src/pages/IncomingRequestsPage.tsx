import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useApiData } from '../hooks/useApiData';
import { requestsApi, type Request } from '../api/requests';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { Chip } from '@heroui/react';
import { Card, CardHeader, CardBody } from '@heroui/react';
import { Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from '@heroui/react';

interface StatsCardProps {
  title: string;
  count: number;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, count, color = 'primary' }) => (
  <Card className="w-full">
    <CardHeader className="flex gap-3">
      <div className="flex flex-col">
        <p className="text-md">{title}</p>
        <p className={`text-2xl font-bold text-${color}`}>{count}</p>
      </div>
    </CardHeader>
  </Card>
);

export const IncomingRequestsPage: React.FC = () => {
  const [mounted, setMounted] = useState(false);

  // Загрузка заявок через существующий хук
  const fetchRequests = useCallback(() => requestsApi.getRequests(), []);
  const { 
    data: requestsData, 
    loading,
    error,
    refetch 
  } = useApiData(fetchRequests, {
    errorMessage: 'Ошибка загрузки заявок'
  });

  const requests = useMemo(() => requestsData || [], [requestsData]);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Фильтрация входящих заявок
  const allowedStatuses = ['Новая', 'Перезвонить', 'ТНО', 'Отказ'];
  const filteredRequests = useMemo(() => {
    return requests.filter((r: Request) => allowedStatuses.includes(r.status));
  }, [requests]);

  // Статистика
  const stats = useMemo(() => {
    const total = filteredRequests.length;
    const newCount = filteredRequests.filter((r: Request) => r.status === 'Новая').length;
    const recallCount = filteredRequests.filter((r: Request) => r.status === 'Перезвонить').length;
    const refusedCount = filteredRequests.filter((r: Request) => r.status === 'Отказ').length;
    const tnoCount = filteredRequests.filter((r: Request) => r.status === 'ТНО').length;

    return { total, newCount, recallCount, refusedCount, tnoCount };
  }, [filteredRequests]);

  // Вспомогательные функции
  const getStatusBadge = useCallback((status: string) => {
    const statusConfig = {
      'Новая': { label: 'Новая', color: 'primary' as const },
      'Перезвонить': { label: 'Перезвон', color: 'warning' as const },
      'ТНО': { label: 'ТНО', color: 'primary' as const },
      'Отказ': { label: 'Отказ', color: 'danger' as const }
    };
    const config = statusConfig[status as keyof typeof statusConfig] || { 
      label: status, 
      color: 'primary' as const 
    };
    return (
      <Chip color={config.color} size="sm" variant="flat">
        {config.label}
      </Chip>
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
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-red-600">
          Ошибка загрузки входящих заявок: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen p-4">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Входящие заявки</h1>
        <p className="text-gray-600">
          Заявки со статусами: Новая, Перезвонить, ТНО, Отказ
        </p>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <StatsCard title="Всего входящих" count={stats.total} color="primary" />
        <StatsCard title="Новые" count={stats.newCount} color="success" />
        <StatsCard title="Перезвон" count={stats.recallCount} color="warning" />
        <StatsCard title="ТНО" count={stats.tnoCount} color="primary" />
        <StatsCard title="Отказы" count={stats.refusedCount} color="danger" />
      </div>

      {/* Таблица на весь экран */}
      <Card className="w-full">
        <CardBody className="p-0">
          <Table 
            aria-label="Таблица входящих заявок"
            className="w-full"
            removeWrapper
            isStriped
          >
            <TableHeader>
              <TableColumn key="id" className="min-w-[60px]">ID</TableColumn>
              <TableColumn key="advertising_campaign" className="min-w-[120px]">РК</TableColumn>
              <TableColumn key="city" className="min-w-[100px]">Город</TableColumn>
              <TableColumn key="request_type" className="min-w-[120px]">Тип заявки</TableColumn>
              <TableColumn key="client_phone" className="min-w-[140px]">Телефон клиента</TableColumn>
              <TableColumn key="client_name" className="min-w-[150px]">Имя клиента</TableColumn>
              <TableColumn key="address" className="min-w-[200px]">Адрес</TableColumn>
              <TableColumn key="meeting_date" className="min-w-[160px]">Дата встречи</TableColumn>
              <TableColumn key="direction" className="min-w-[120px]">Направление</TableColumn>
              <TableColumn key="problem" className="min-w-[200px]">Проблема</TableColumn>
              <TableColumn key="status" className="min-w-[100px]">Статус</TableColumn>
              <TableColumn key="ats_number" className="min-w-[100px]">Номер АТС</TableColumn>
              <TableColumn key="call_center_name" className="min-w-[120px]">Имя КЦ</TableColumn>
              <TableColumn key="call_center_notes" className="min-w-[200px]">Заметка КЦ</TableColumn>
            </TableHeader>
            <TableBody emptyContent="Входящие заявки не найдены">
              {filteredRequests.map((request: Request) => (
                <TableRow key={request.id}>
                  <TableCell>{request.id}</TableCell>
                  <TableCell>{request.advertising_campaign?.name || '-'}</TableCell>
                  <TableCell>{request.city?.name || '-'}</TableCell>
                  <TableCell>{request.request_type?.name || '-'}</TableCell>
                  <TableCell>{request.client_phone || '-'}</TableCell>
                  <TableCell>{request.client_name || '-'}</TableCell>
                  <TableCell>
                    <div className="max-w-[200px] truncate" title={request.address || '-'}>
                      {request.address || '-'}
                    </div>
                  </TableCell>
                  <TableCell>{formatDate(request.meeting_date)}</TableCell>
                  <TableCell>{request.direction?.name || '-'}</TableCell>
                  <TableCell>
                    <div className="max-w-[200px] truncate" title={request.problem || '-'}>
                      {request.problem || '-'}
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(request.status)}</TableCell>
                  <TableCell>{request.ats_number || '-'}</TableCell>
                  <TableCell>{request.call_center_name || '-'}</TableCell>
                  <TableCell>
                    <div className="max-w-[200px] truncate" title={request.call_center_notes || '-'}>
                      {request.call_center_notes || '-'}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}; 