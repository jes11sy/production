import React, { useState, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Card,
  Input,
  Button,
  Divider,
  Textarea,
  Spinner,
  Badge,
  Select,
  SelectItem
} from '@heroui/react';
import {
  ArrowLeftIcon,
  DocumentTextIcon,
  UserIcon,
  BuildingOfficeIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { requestsApi, type CreateRequest } from '../api/requests';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData } from '../hooks/useApiData';
import { useNotification } from '../contexts/NotificationContext';
import dayjs from 'dayjs';

const IncomingRequestEditPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const requestId = parseInt(id || '0');
  const { showSuccess, showError } = useNotification();
  
  const { cities, requestTypes, directions } = useAppData();
  
  const [updateLoading, setUpdateLoading] = useState(false);
  const [editForm, setEditForm] = useState<CreateRequest & { status: string }>({
    advertising_campaign_id: undefined,
    client_name: '',
    client_phone: '',
    city_id: 0,
    request_type_id: 0,
    address: '',
    meeting_date: '',
    direction_id: undefined,
    problem: '',
    status: 'new',
    ats_number: '',
    call_center_name: '',
    call_center_notes: ''
  });

  const loadRequestData = useCallback(async () => {
    const requestData = await requestsApi.getRequest(requestId);
    setEditForm({
      advertising_campaign_id: requestData.advertising_campaign_id || undefined,
      client_name: requestData.client_name || '',
      client_phone: requestData.client_phone || '',
      city_id: requestData.city_id || 0,
      request_type_id: requestData.request_type_id || 0,
      address: requestData.address || '',
      meeting_date: requestData.meeting_date || '',
      direction_id: requestData.direction_id || undefined,
      problem: requestData.problem || '',
      status: requestData.status || 'new',
      ats_number: requestData.ats_number || '',
      call_center_name: requestData.call_center_name || '',
      call_center_notes: requestData.call_center_notes || ''
    });
    return requestData;
  }, [requestId]);

  const { data: request, loading, error } = useApiData(loadRequestData);

  const handleUpdateRequest = useCallback(async () => {
    try {
      setUpdateLoading(true);
      await requestsApi.updateRequest(requestId, editForm);
      showSuccess('Заявка успешно обновлена');
      navigate('/incoming-requests');
    } catch (error) {
      console.error('Error updating request:', error);
      showError('Ошибка обновления заявки');
    } finally {
      setUpdateLoading(false);
    }
  }, [requestId, editForm, showSuccess, showError, navigate]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleUpdateRequest();
  }, [handleUpdateRequest]);

  const handleInputChange = useCallback((field: keyof (CreateRequest & { status: string }), value: any) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  }, []);

  const dateFormat = 'DD.MM.YY HH:mm';

  const statusBadgeColor = useMemo(() => {
    switch (editForm.status) {
      case 'new': return 'primary';
      case 'recall': return 'warning';
      case 'tno': return 'secondary';
      case 'refused': return 'danger';
      case 'waiting': return 'default';
      default: return 'default';
    }
  }, [editForm.status]);

  const statusLabel = useMemo(() => {
    switch (editForm.status) {
      case 'new': return 'Новая';
      case 'recall': return 'Перезвонить';
      case 'tno': return 'ТНО';
      case 'refused': return 'Отказ';
      case 'waiting': return 'Ожидает';
      default: return editForm.status;
    }
  }, [editForm.status]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4">
        <Card className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-2xl">
          {error}
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-2 py-10">
      <Card className="rounded-3xl shadow-2xl border-0 bg-white/90 p-10">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="light"
            startContent={<ArrowLeftIcon className="h-5 w-5" />}
            onClick={() => navigate('/incoming-requests')}
            className="!px-4 !py-2"
          >
            Назад
          </Button>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center rounded-full bg-blue-100 text-blue-700 mr-2 p-2">
              <DocumentTextIcon className="h-7 w-7" />
            </span>
            <h2 className="text-2xl font-bold mb-0">Редактировать заявку #{requestId}</h2>
            <Badge color={statusBadgeColor}>{statusLabel}</Badge>
          </div>
        </div>
        <Divider className="mb-8" />
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            {/* Секция: Клиент */}
            <div className="space-y-6">
              <h5 className="text-gray-500 mb-2 flex items-center gap-2 text-lg font-semibold">
                <UserIcon className="h-5 w-5" /> Клиент
              </h5>
              <Input 
                label="Имя клиента *" 
                value={editForm.client_name} 
                onChange={e => handleInputChange('client_name', e.target.value)} 
                fullWidth 
                required 
                size="md" 
              />
              <Input 
                label="Телефон клиента *" 
                value={editForm.client_phone} 
                onChange={e => handleInputChange('client_phone', e.target.value)} 
                fullWidth 
                required 
                size="md" 
              />
              <Select
                label="Город *"
                placeholder="Выберите город"
                selectedKeys={editForm.city_id ? [String(editForm.city_id)] : []}
                onSelectionChange={(keys) => {
                  const selectedKey = Array.from(keys)[0];
                  handleInputChange('city_id', selectedKey ? Number(selectedKey) : 0);
                }}
                isRequired
              >
                {cities.map(city => (
                  <SelectItem key={city.id} value={city.id}>{city.name}</SelectItem>
                ))}
              </Select>
              <Input 
                label="Адрес" 
                value={editForm.address || ''} 
                onChange={e => handleInputChange('address', e.target.value)} 
                fullWidth 
                size="md" 
              />
            </div>
            
            {/* Секция: Детали заявки */}
            <div className="space-y-6">
              <h5 className="text-gray-500 mb-2 flex items-center gap-2 text-lg font-semibold">
                <DocumentTextIcon className="h-5 w-5" /> Детали
              </h5>
              <Select
                label="Рекламная кампания"
                placeholder="Выберите кампанию"
                selectedKeys={editForm.advertising_campaign_id ? [String(editForm.advertising_campaign_id)] : []}
                onSelectionChange={(keys) => {
                  const selectedKey = Array.from(keys)[0];
                  handleInputChange('advertising_campaign_id', selectedKey ? Number(selectedKey) : undefined);
                }}
              >
                {advertisingCampaigns.map(campaign => (
                  <SelectItem key={campaign.id} value={campaign.id}>
                    {campaign.name}{campaign.city ? ` (${campaign.city.name})` : ''}
                  </SelectItem>
                ))}
              </Select>
              <Select
                label="Тип заявки *"
                placeholder="Выберите тип"
                selectedKeys={editForm.request_type_id ? [String(editForm.request_type_id)] : []}
                onSelectionChange={(keys) => {
                  const selectedKey = Array.from(keys)[0];
                  handleInputChange('request_type_id', selectedKey ? Number(selectedKey) : 0);
                }}
                isRequired
              >
                {requestTypes.map(type => (
                  <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
                ))}
              </Select>
              <Input
                label="Дата встречи"
                placeholder="01.01.01 01:01"
                value={editForm.meeting_date ? dayjs(editForm.meeting_date).format(dateFormat) : ''}
                onChange={e => handleInputChange('meeting_date', e.target.value)}
                fullWidth
                size="md"
              />
              <Select
                label="Направление"
                placeholder="Выберите направление"
                selectedKeys={editForm.direction_id ? [String(editForm.direction_id)] : []}
                onSelectionChange={(keys) => {
                  const selectedKey = Array.from(keys)[0];
                  handleInputChange('direction_id', selectedKey ? Number(selectedKey) : undefined);
                }}
              >
                {directions.map(direction => (
                  <SelectItem key={direction.id} value={direction.id}>{direction.name}</SelectItem>
                ))}
              </Select>
              <Textarea
                label="Описание проблемы"
                value={editForm.problem || ''}
                onChange={e => handleInputChange('problem', e.target.value)}
                fullWidth
                minRows={3}
                size="md"
              />
              <Select
                label="Статус"
                selectedKeys={[editForm.status]}
                onSelectionChange={(keys) => {
                  const selectedKey = Array.from(keys)[0];
                  handleInputChange('status', selectedKey);
                }}
              >
                <SelectItem key="new" value="new">Новая</SelectItem>
                <SelectItem key="recall" value="recall">Перезвонить</SelectItem>
                <SelectItem key="tno" value="tno">ТНО</SelectItem>
                <SelectItem key="refused" value="refused">Отказ</SelectItem>
                <SelectItem key="waiting" value="waiting">Ожидает</SelectItem>
              </Select>
            </div>
          </div>
          <Divider className="my-10" />
          {/* Секция: КЦ */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-8">
            <div className="space-y-6">
              <h5 className="text-gray-500 mb-2 flex items-center gap-2 text-lg font-semibold">
                <BuildingOfficeIcon className="h-5 w-5" /> Колл-центр
              </h5>
              <Input 
                label="Номер АТС" 
                value={editForm.ats_number || ''} 
                onChange={e => handleInputChange('ats_number', e.target.value)} 
                fullWidth 
                size="md" 
              />
              <Input 
                label="Имя КЦ" 
                value={editForm.call_center_name || ''} 
                onChange={e => handleInputChange('call_center_name', e.target.value)} 
                fullWidth 
                size="md" 
              />
              <Textarea 
                label="Заметка КЦ" 
                value={editForm.call_center_notes || ''} 
                onChange={e => handleInputChange('call_center_notes', e.target.value)} 
                fullWidth 
                minRows={2} 
                size="md" 
              />
            </div>
          </div>
          <div className="flex justify-end gap-4 mt-8">
            <Button 
              variant="light" 
              size="lg" 
              startContent={<ArrowLeftIcon className="h-5 w-5" />} 
              onClick={() => navigate('/incoming-requests')}
            >
              Отмена
            </Button>
            <Button 
              color="primary" 
              size="lg" 
              isLoading={updateLoading} 
              type="submit" 
              startContent={<CheckCircleIcon className="h-5 w-5" />}
            >
              Сохранить изменения
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default IncomingRequestEditPage; 