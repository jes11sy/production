import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { requestsApi, type Request, type CreateRequest } from '../api/requests';

// Используем CreateRequest из API
type CreateRequestForm = CreateRequest;
import { advertisingCampaignsApi } from '../api/advertisingCampaigns';
import type { AdvertisingCampaign } from '../types/api';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData, useMultipleApiData } from '../hooks/useApiData';
import { useNotification } from '../contexts/NotificationContext';

import {
  FunnelIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  PhoneIcon,
  UserIcon,
  MapPinIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import {
  Card,
  Input,
  Button,
  Chip,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Spinner,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Select,
  SelectItem,
  Textarea,
  useDisclosure
} from '@heroui/react';

const IncomingRequestsPage: React.FC = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { cities, requestTypes, directions, loading: appDataLoading } = useAppData();

  // Загрузка заявок
  const fetchRequests = useCallback(() => requestsApi.getRequests(), []);
  const { 
    data: requestsData, 
    loading: requestsLoading,
    refetch: refetchRequests
  } = useApiData(fetchRequests, {
    errorMessage: 'Ошибка загрузки заявок'
  });

  // Загрузка дополнительных данных
  const additionalApiCalls = useMemo(() => ({
    advertisingCampaigns: () => advertisingCampaignsApi.getAdvertisingCampaigns()
  }), []);
  
  const { 
    data: additionalData,
    loading: additionalLoading 
  } = useMultipleApiData(additionalApiCalls, {
    errorMessage: 'Ошибка загрузки рекламных кампаний'
  });

  // Мемоизированные данные
  const requests = useMemo(() => requestsData || [], [requestsData]);
  const advertisingCampaigns = useMemo(() => additionalData?.advertisingCampaigns || [], [additionalData?.advertisingCampaigns]);

  // Состояние создания заявки
  const [createLoading, setCreateLoading] = useState(false);
  const [createForm, setCreateForm] = useState<CreateRequestForm>({
    client_name: '',
    client_phone: '',
    city_id: undefined,
    request_type_id: undefined,
    address: '',
    problem: '',
    advertising_campaign_id: undefined,
    direction_id: undefined,
    meeting_date: ''
  });

  // Общий индикатор загрузки
  const isLoading = requestsLoading || additionalLoading || appDataLoading.cities || appDataLoading.requestTypes;

  // Фильтрация входящих заявок
  const allowedStatuses = ['Новая', 'Перезвонить', 'ТНО', 'Отказ'];
  const filteredRequests = useMemo(() => {
    return requests.filter(r => allowedStatuses.includes(r.status));
  }, [requests]);

  // Обработчики форм
  const handleFormChange = useCallback((field: keyof CreateRequestForm, value: string | number | undefined) => {
    setCreateForm(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleCreateRequest = useCallback(async () => {
    try {
      setCreateLoading(true);
      
      // Валидация обязательных полей
      if (!createForm.client_name || !createForm.client_phone || !createForm.city_id || !createForm.request_type_id) {
        showError('Заполните обязательные поля');
        return;
      }

      await requestsApi.createRequest(createForm);
      
      // Сброс формы
      setCreateForm({
        client_name: '',
        client_phone: '',
        city_id: undefined,
        request_type_id: undefined,
        address: '',
        problem: '',
        advertising_campaign_id: undefined,
        direction_id: undefined,
        meeting_date: ''
      });
      
      onClose();
      showSuccess('Заявка успешно создана');
      refetchRequests();
    } catch (error) {
      showError('Ошибка создания заявки');
    } finally {
      setCreateLoading(false);
    }
  }, [createForm, showSuccess, showError, onClose, refetchRequests]);

  // Обработчики действий
  const handleRowClick = useCallback((requestId: number) => {
    navigate(`/incoming-requests/${requestId}/edit`);
  }, [navigate]);

  const handleOpenCreateModal = useCallback(() => {
    onOpen();
  }, [onOpen]);

  // Вспомогательные функции
  const getStatusBadge = useCallback((status: string) => {
    const statusConfig = {
      'Новая': { label: 'Новая', color: 'primary' as const },
      'Перезвонить': { label: 'Перезвон', color: 'warning' as const },
      'ТНО': { label: 'ТНО', color: 'secondary' as const },
      'Отказ': { label: 'Отказ', color: 'danger' as const }
    };
    const config = statusConfig[status as keyof typeof statusConfig] || { 
      label: status, 
      color: 'default' as const 
    };
    return (
      <Chip color={config.color} size="sm" variant="flat">
        {config.label}
      </Chip>
    );
  }, []);

  const formatDate = useCallback((dateString: string) => {
    return dateString ? new Date(dateString).toLocaleDateString('ru-RU') : '-';
  }, []);

  // Отображение загрузки
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Входящие заявки</h1>
            <p className="mt-2 text-gray-600">Новые заявки для обработки</p>
          </div>
          <Button
            color="primary"
            startContent={<PlusIcon className="w-5 h-5" />}
            onPress={handleOpenCreateModal}
          >
            Новая заявка
          </Button>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="p-4">
          <div className="flex items-center">
            <DocumentTextIcon className="w-8 h-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Всего входящих</p>
              <p className="text-2xl font-bold text-gray-900">{filteredRequests.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Новые</p>
              <p className="text-2xl font-bold text-blue-600">
                {filteredRequests.filter(r => r.status === 'Новая').length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Перезвон</p>
              <p className="text-2xl font-bold text-yellow-600">
                {filteredRequests.filter(r => r.status === 'Перезвонить').length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Отказы</p>
              <p className="text-2xl font-bold text-red-600">
                {filteredRequests.filter(r => r.status === 'Отказ').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Таблица заявок */}
      <Card>
        <Table 
          aria-label="Таблица входящих заявок"
          classNames={{
            wrapper: "min-h-[400px]",
          }}
        >
          <TableHeader>
            <TableColumn>
              <div className="flex items-center gap-2">
                <UserIcon className="w-4 h-4" />
                КЛИЕНТ
              </div>
            </TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <PhoneIcon className="w-4 h-4" />
                ТЕЛЕФОН
              </div>
            </TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <MapPinIcon className="w-4 h-4" />
                АДРЕС
              </div>
            </TableColumn>
            <TableColumn>
              <div className="flex items-center gap-2">
                <CalendarIcon className="w-4 h-4" />
                ДАТА СОЗДАНИЯ
              </div>
            </TableColumn>
            <TableColumn>СТАТУС</TableColumn>
            <TableColumn>ПРОБЛЕМА</TableColumn>
          </TableHeader>
          <TableBody
            emptyContent={
              <div className="flex flex-col items-center justify-center py-8">
                <DocumentTextIcon className="h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-500 text-lg">Входящие заявки не найдены</p>
                <p className="text-gray-400 text-sm">Создайте новую заявку или проверьте фильтры</p>
              </div>
            }
          >
            {filteredRequests.map((request) => (
              <TableRow 
                key={request.id}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleRowClick(request.id)}
              >
                <TableCell>
                  <div>
                    <div className="font-medium">{request.client_name}</div>
                    <div className="text-sm text-gray-500">{request.city.name}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="font-mono">{request.client_phone}</div>
                </TableCell>
                <TableCell>
                  <div className="max-w-xs truncate">{request.address || '-'}</div>
                </TableCell>
                <TableCell>
                  <div>{formatDate(request.created_at)}</div>
                </TableCell>
                <TableCell>
                  {getStatusBadge(request.status)}
                </TableCell>
                <TableCell>
                  <div className="max-w-xs truncate">{request.problem || '-'}</div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Модальное окно создания заявки */}
      <Modal isOpen={isOpen} onClose={onClose} size="2xl">
        <ModalContent>
          <ModalHeader>Создать новую заявку</ModalHeader>
          <ModalBody>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Имя клиента *"
                placeholder="Введите имя клиента"
                value={createForm.client_name}
                onValueChange={(value) => handleFormChange('client_name', value)}
                isRequired
              />
              
              <Input
                label="Телефон клиента *"
                placeholder="+7 (999) 999-99-99"
                value={createForm.client_phone}
                onValueChange={(value) => handleFormChange('client_phone', value)}
                isRequired
              />
              
              <Select
                label="Город *"
                placeholder="Выберите город"
                selectedKeys={createForm.city_id ? [createForm.city_id.toString()] : []}
                onSelectionChange={(keys) => {
                  const value = Array.from(keys)[0] as string;
                  handleFormChange('city_id', value ? parseInt(value) : undefined);
                }}
                isRequired
              >
                {cities.map((city) => (
                  <SelectItem key={city.id.toString()}>
                    {city.name}
                  </SelectItem>
                ))}
              </Select>
              
              <Select
                label="Тип заявки *"
                placeholder="Выберите тип заявки"
                selectedKeys={createForm.request_type_id ? [createForm.request_type_id.toString()] : []}
                onSelectionChange={(keys) => {
                  const value = Array.from(keys)[0] as string;
                  handleFormChange('request_type_id', value ? parseInt(value) : undefined);
                }}
                isRequired
              >
                {requestTypes.map((type) => (
                  <SelectItem key={type.id.toString()}>
                    {type.name}
                  </SelectItem>
                ))}
              </Select>
              
              <Select
                label="Рекламная кампания"
                placeholder="Выберите РК (необязательно)"
                selectedKeys={createForm.advertising_campaign_id ? [createForm.advertising_campaign_id.toString()] : []}
                onSelectionChange={(keys) => {
                  const value = Array.from(keys)[0] as string;
                  handleFormChange('advertising_campaign_id', value ? parseInt(value) : undefined);
                }}
              >
                {advertisingCampaigns.map((campaign) => (
                  <SelectItem key={campaign.id.toString()}>
                    {campaign.name}
                  </SelectItem>
                ))}
              </Select>
              
              <Select
                label="Направление"
                placeholder="Выберите направление (необязательно)"
                selectedKeys={createForm.direction_id ? [createForm.direction_id.toString()] : []}
                onSelectionChange={(keys) => {
                  const value = Array.from(keys)[0] as string;
                  handleFormChange('direction_id', value ? parseInt(value) : undefined);
                }}
              >
                {directions.map((direction) => (
                  <SelectItem key={direction.id.toString()}>
                    {direction.name}
                  </SelectItem>
                ))}
              </Select>
            </div>
            
            <Input
              label="Адрес"
              placeholder="Введите адрес клиента"
              value={createForm.address || ''}
              onValueChange={(value) => handleFormChange('address', value)}
              className="mt-4"
            />
            
            <Input
              label="Дата встречи"
              type="datetime-local"
              value={createForm.meeting_date || ''}
              onValueChange={(value) => handleFormChange('meeting_date', value)}
              className="mt-4"
            />
            
            <Textarea
              label="Описание проблемы"
              placeholder="Опишите проблему клиента"
              value={createForm.problem || ''}
              onValueChange={(value) => handleFormChange('problem', value)}
              minRows={3}
              className="mt-4"
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onClose}>
              Отмена
            </Button>
            <Button 
              color="primary" 
              onPress={handleCreateRequest}
              isLoading={createLoading}
            >
              Создать заявку
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default IncomingRequestsPage; 