import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Input,
  Button,
  Select,
  SelectItem,
  Card,
  Chip,
  Spinner
} from '@heroui/react';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  UserIcon,
  PhoneIcon,
  MapPinIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { usersApi } from '../api/users';
import { useApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import type { Master } from '../types/api';
import dayjs from 'dayjs';

// Интерфейс для фильтров
interface MasterFilters {
  search: string;
  status: string;
  city: string;
}

const MastersPage: React.FC = () => {
  const navigate = useNavigate();
  const { cities } = useAppData();
  
  const [filters, setFilters] = useState<MasterFilters>({
    search: '',
    status: 'all',
    city: 'all'
  });

  // Загрузка мастеров
  const getMasters = useCallback(() => usersApi.getMasters(), []);
  
  const { 
    data: mastersData, 
    loading: mastersLoading 
  } = useApiData(getMasters, {
    errorMessage: 'Ошибка загрузки мастеров'
  });

  // Мемоизированная фильтрация мастеров
  const filteredMasters = useMemo(() => {
    if (!mastersData) return [];
    
    return mastersData.filter(master => {
      const matchesSearch = master.full_name.toLowerCase().includes(filters.search.toLowerCase()) ||
                           master.phone_number.includes(filters.search) ||
                           master.login.toLowerCase().includes(filters.search.toLowerCase());
      
      const matchesStatus = filters.status === 'all' || master.status === filters.status;
      const matchesCity = filters.city === 'all' || master.city_id === parseInt(filters.city);

      return matchesSearch && matchesStatus && matchesCity;
    });
  }, [mastersData, filters]);

     // Статистика мастеров
   const masterStats = useMemo(() => {
     if (!mastersData) {
       return { 
         total: 0, 
         active: 0, 
         inactive: 0, 
         busy: 0,
         citiesCount: 0 
       };
     }
     
     const active = mastersData.filter(m => m.status === 'active').length;
     const inactive = mastersData.filter(m => m.status === 'inactive').length;
     const busy = mastersData.filter(m => m.status === 'busy').length;
     const uniqueCities = new Set(mastersData.map(m => m.city_id));
     
     return {
       total: mastersData.length,
       active,
       inactive,
       busy,
       citiesCount: uniqueCities.size
     };
   }, [mastersData]);

  // Мемоизированные обработчики
  const handleFilterChange = useCallback((key: keyof MasterFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleResetFilters = useCallback(() => {
    setFilters({
      search: '',
      status: 'all',
      city: 'all'
    });
  }, []);

  // Вспомогательные функции
  const getCityName = useCallback((cityId: number) => {
    return cities.find(c => c.id === cityId)?.name || '—';
  }, [cities]);

     const getStatusConfig = useCallback((status: string) => {
     const configs = {
       'active': { 
         label: 'Активен', 
         color: 'success' as const,
         icon: <CheckCircleIcon className="h-4 w-4" />
       },
       'inactive': { 
         label: 'Неактивен', 
         color: 'danger' as const,
         icon: <XCircleIcon className="h-4 w-4" />
       },
       'busy': { 
         label: 'Занят', 
         color: 'warning' as const,
         icon: <ClockIcon className="h-4 w-4" />
       }
     };

     return configs[status as keyof typeof configs] || { 
       label: status, 
       color: 'default' as const,
       icon: null
     };
   }, []);

  const formatDate = useCallback((dateString: string) => {
    return dayjs(dateString).format('DD.MM.YYYY');
  }, []);

  // Мемоизированный рендер строки мастера
  const renderMasterRow = useCallback((master: Master) => {
    const statusConfig = getStatusConfig(master.status);
    
    return (
      <TableRow 
        key={master.id}
        className="cursor-pointer"
        onClick={() => navigate(`/masters/${master.id}`)}
      >
        <TableCell>{master.id}</TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <UserIcon className="h-4 w-4 text-gray-400" />
            {master.full_name}
          </div>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <PhoneIcon className="h-4 w-4 text-green-500" />
            <a 
              href={`tel:${master.phone_number}`}
              className="text-blue-600 hover:text-blue-800"
              onClick={(e) => e.stopPropagation()}
            >
              {master.phone_number}
            </a>
          </div>
        </TableCell>
        <TableCell>{master.login}</TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <MapPinIcon className="h-4 w-4 text-gray-400" />
            {getCityName(master.city_id)}
          </div>
        </TableCell>
        <TableCell>
          <Chip 
            color={statusConfig.color}
            size="sm"
            startContent={statusConfig.icon}
          >
            {statusConfig.label}
          </Chip>
        </TableCell>
        <TableCell>
          {master.birth_date ? formatDate(master.birth_date) : '—'}
        </TableCell>
        <TableCell>
          {formatDate(master.created_at)}
        </TableCell>
      </TableRow>
    );
  }, [navigate, getCityName, getStatusConfig, formatDate]);

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold">Мастера</h1>
            <p className="text-gray-600">Управление списком мастеров</p>
          </div>
          <Button
            color="primary"
            onClick={() => navigate('/masters/create')}
            startContent={<PlusIcon className="h-4 w-4" />}
          >
            Новый мастер
          </Button>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <UserIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Всего</p>
                <p className="text-2xl font-bold">{masterStats.total}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircleIcon className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Активных</p>
                <p className="text-2xl font-bold text-green-600">{masterStats.active}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <XCircleIcon className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Неактивных</p>
                <p className="text-2xl font-bold text-red-600">{masterStats.inactive}</p>
              </div>
            </div>
          </Card>
          
                     <Card className="p-4">
             <div className="flex items-center gap-3">
               <div className="p-2 bg-yellow-100 rounded-lg">
                 <ClockIcon className="h-6 w-6 text-yellow-600" />
               </div>
               <div>
                 <p className="text-sm text-gray-600">Занятых</p>
                 <p className="text-2xl font-bold text-yellow-600">{masterStats.busy}</p>
               </div>
             </div>
           </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <MapPinIcon className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Городов</p>
                <p className="text-2xl font-bold text-purple-600">{masterStats.citiesCount}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Фильтры */}
        <Card className="mb-4">
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Input
                label="Поиск"
                placeholder="Имя, телефон, логин..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                startContent={<MagnifyingGlassIcon className="h-4 w-4" />}
              />
              
                             <Select
                 label="Статус"
                 placeholder="Все статусы"
                 selectedKeys={filters.status !== 'all' ? [filters.status] : []}
                 onSelectionChange={(keys) => 
                   handleFilterChange('status', Array.from(keys)[0] as string || 'all')
                 }
               >
                 <SelectItem key="active">Активен</SelectItem>
                 <SelectItem key="inactive">Неактивен</SelectItem>
                 <SelectItem key="busy">Занят</SelectItem>
               </Select>
              
              <Select
                label="Город"
                placeholder="Все города"
                selectedKeys={filters.city !== 'all' ? [filters.city] : []}
                onSelectionChange={(keys) => 
                  handleFilterChange('city', Array.from(keys)[0] as string || 'all')
                }
                isLoading={!cities.length}
              >
                {cities.map(city => (
                  <SelectItem key={city.id}>
                    {city.name}
                  </SelectItem>
                ))}
              </Select>
              
              <div className="flex items-end">
                <Button
                  variant="bordered"
                  onClick={handleResetFilters}
                  className="w-full"
                >
                  Сбросить
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Основная таблица */}
      <Card>
        <div className="p-4">
          <Table aria-label="Таблица мастеров">
            <TableHeader>
              <TableColumn>ID</TableColumn>
              <TableColumn>ФИО</TableColumn>
              <TableColumn>Телефон</TableColumn>
              <TableColumn>Логин</TableColumn>
              <TableColumn>Город</TableColumn>
              <TableColumn>Статус</TableColumn>
              <TableColumn>Дата рождения</TableColumn>
              <TableColumn>Дата создания</TableColumn>
            </TableHeader>
            <TableBody
              isLoading={mastersLoading}
              loadingContent={<Spinner />}
              emptyContent="Мастеры не найдены"
            >
              {filteredMasters.map(renderMasterRow)}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  );
};

export default MastersPage; 