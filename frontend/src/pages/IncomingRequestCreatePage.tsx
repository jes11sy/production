import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Input,
  Button,
  Select,
  SelectItem,
  Card,
  Textarea
} from '@heroui/react';
import { 
  ArrowLeftIcon,
  PhoneIcon,
  UserIcon,
  MapPinIcon,
  CalendarIcon,
  DocumentTextIcon,
  TagIcon,
  BuildingOfficeIcon,
  MegaphoneIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAppData } from '../contexts/AppDataContext';
import { useNotification } from '../contexts/NotificationContext';
import { useApiData } from '../hooks/useApiData';
import { requestsApi } from '../api/requests';
import { advertisingCampaignsApi } from '../api/advertisingCampaigns';
import type { CreateRequestData } from '../types/api';
import dayjs from 'dayjs';

const schema = z.object({
  advertising_campaign_id: z.number().optional(),
  city_id: z.number().min(1, 'Выберите город'),
  request_type_id: z.number().min(1, 'Выберите тип заявки'),
  client_phone: z.string().min(1, 'Введите телефон клиента'),
  client_name: z.string().min(1, 'Введите имя клиента'),
  address: z.string().optional(),
  meeting_date: z.string().optional(),
  direction_id: z.number().optional(),
  problem: z.string().optional(),
  status: z.enum(['new', 'recall', 'tno', 'refused', 'waiting']),
  ats_number: z.string().optional(),
  call_center_name: z.string().optional(),
  call_center_notes: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

const IncomingRequestCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { cities, requestTypes, directions } = useAppData();
  const { showSuccess, showError } = useNotification();
  const [creating, setCreating] = useState(false);

  // Load advertising campaigns
  const fetchCampaigns = useCallback(() => advertisingCampaignsApi.getAdvertisingCampaigns(), []);
  const { 
    data: campaigns, 
    loading: campaignsLoading 
  } = useApiData(fetchCampaigns);

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      status: 'new',
      meeting_date: dayjs().format('YYYY-MM-DDTHH:mm'),
    }
  });

  const handleCancel = useCallback(() => {
    navigate('/incoming-requests');
  }, [navigate]);

  const onSubmit = useCallback(async (data: FormData) => {
    setCreating(true);
    try {
      const requestData: CreateRequestData = {
        advertising_campaign_id: data.advertising_campaign_id,
        client_name: data.client_name,
        client_phone: data.client_phone,
        city_id: data.city_id,
        request_type_id: data.request_type_id,
        address: data.address,
        meeting_date: data.meeting_date,
        direction_id: data.direction_id,
        problem: data.problem
      };

      await requestsApi.createRequest(requestData);
      showSuccess('Заявка создана успешно');
      navigate('/incoming-requests');
    } catch (error) {
      console.error('Error creating request:', error);
      showError('Ошибка создания заявки');
    } finally {
      setCreating(false);
    }
  }, [showSuccess, showError, navigate]);

  // Memoized handlers for form fields
  const handleCampaignChange = useCallback((keys: any) => {
    const value = Array.from(keys)[0];
    setValue('advertising_campaign_id', value ? Number(value) : undefined);
  }, [setValue]);

  const handleCityChange = useCallback((keys: any) => {
    const cityId = Array.from(keys)[0];
    setValue('city_id', Number(cityId));
  }, [setValue]);

  const handleRequestTypeChange = useCallback((keys: any) => {
    const typeId = Array.from(keys)[0];
    setValue('request_type_id', Number(typeId));
  }, [setValue]);

  const handleDirectionChange = useCallback((keys: any) => {
    const value = Array.from(keys)[0];
    setValue('direction_id', value ? Number(value) : undefined);
  }, [setValue]);

  const handleStatusChange = useCallback((keys: any) => {
    const status = Array.from(keys)[0] as 'new' | 'recall' | 'tno' | 'refused' | 'waiting';
    setValue('status', status);
  }, [setValue]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="light"
          startContent={<ArrowLeftIcon className="h-4 w-4" />}
          onClick={handleCancel}
        >
          Назад к списку
        </Button>
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center rounded-full bg-orange-100 text-orange-700 p-3">
            <ClipboardDocumentListIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Новая заявка</h1>
            <p className="text-gray-600">Создание входящей заявки</p>
          </div>
        </div>
      </div>

      {/* Form */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <ClipboardDocumentListIcon className="h-6 w-6 text-gray-600" />
          <h2 className="text-xl font-semibold">Информация о заявке</h2>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Client Information Section */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h3 className="text-lg font-medium text-blue-900 mb-4 flex items-center gap-2">
              <UserIcon className="h-5 w-5" />
              Информация о клиенте
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Телефон клиента"
                placeholder="+7 (999) 123-45-67"
                type="tel"
                {...register('client_phone')}
                isInvalid={!!errors.client_phone}
                errorMessage={errors.client_phone?.message}
                variant="bordered"
                isRequired
                startContent={<PhoneIcon className="h-4 w-4 text-gray-400" />}
              />
              
              <Input
                label="Имя клиента"
                placeholder="Введите имя клиента"
                {...register('client_name')}
                isInvalid={!!errors.client_name}
                errorMessage={errors.client_name?.message}
                variant="bordered"
                isRequired
                startContent={<UserIcon className="h-4 w-4 text-gray-400" />}
              />
            </div>
          </div>

          {/* Request Details Section */}
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <h3 className="text-lg font-medium text-green-900 mb-4 flex items-center gap-2">
              <TagIcon className="h-5 w-5" />
              Детали заявки
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Город"
                placeholder="Выберите город"
                selectedKeys={watch('city_id') ? [String(watch('city_id'))] : []}
                onSelectionChange={handleCityChange}
                isInvalid={!!errors.city_id}
                errorMessage={errors.city_id?.message}
                variant="bordered"
                isRequired
                startContent={<BuildingOfficeIcon className="h-4 w-4 text-gray-400" />}
              >
                {cities.map(city => (
                  <SelectItem key={city.id.toString()}>
                    {city.name}
                  </SelectItem>
                ))}
              </Select>

              <Select
                label="Тип заявки"
                placeholder="Выберите тип заявки"
                selectedKeys={watch('request_type_id') ? [String(watch('request_type_id'))] : []}
                onSelectionChange={handleRequestTypeChange}
                isInvalid={!!errors.request_type_id}
                errorMessage={errors.request_type_id?.message}
                variant="bordered"
                isRequired
                startContent={<TagIcon className="h-4 w-4 text-gray-400" />}
              >
                {requestTypes.map(type => (
                  <SelectItem key={type.id.toString()}>
                    {type.name}
                  </SelectItem>
                ))}
              </Select>

              <Select
                label="Направление"
                placeholder="Выберите направление"
                selectedKeys={watch('direction_id') ? [String(watch('direction_id'))] : []}
                onSelectionChange={handleDirectionChange}
                variant="bordered"
              >
                {directions.map(direction => (
                  <SelectItem key={direction.id.toString()}>
                    {direction.name}
                  </SelectItem>
                ))}
              </Select>

              <Select
                label="Статус"
                placeholder="Выберите статус"
                selectedKeys={watch('status') ? [watch('status')] : []}
                onSelectionChange={handleStatusChange}
                variant="bordered"
              >
                <SelectItem key="new">Новая</SelectItem>
                <SelectItem key="recall">Перезвонить</SelectItem>
                <SelectItem key="tno">ТНО</SelectItem>
                <SelectItem key="refused">Отказ</SelectItem>
                <SelectItem key="waiting">Ожидает</SelectItem>
              </Select>
            </div>
          </div>

          {/* Marketing Section */}
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <h3 className="text-lg font-medium text-purple-900 mb-4 flex items-center gap-2">
              <MegaphoneIcon className="h-5 w-5" />
              Реклама и источник
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Рекламная кампания"
                placeholder="Выберите кампанию"
                selectedKeys={watch('advertising_campaign_id') ? [String(watch('advertising_campaign_id'))] : []}
                onSelectionChange={handleCampaignChange}
                variant="bordered"
                isLoading={campaignsLoading}
                startContent={<MegaphoneIcon className="h-4 w-4 text-gray-400" />}
              >
                {campaigns?.map(campaign => (
                  <SelectItem key={campaign.id.toString()}>
                    {campaign.name} ({campaign.city?.name})
                  </SelectItem>
                )) || []}
              </Select>

              <Input
                label="Номер АТС"
                placeholder="Введите номер АТС"
                {...register('ats_number')}
                variant="bordered"
              />
            </div>
          </div>

          {/* Additional Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Input
                label="Адрес"
                placeholder="Введите адрес клиента"
                {...register('address')}
                variant="bordered"
                startContent={<MapPinIcon className="h-4 w-4 text-gray-400" />}
              />

              <Input
                label="Дата встречи"
                type="datetime-local"
                {...register('meeting_date')}
                variant="bordered"
                startContent={<CalendarIcon className="h-4 w-4 text-gray-400" />}
              />

              <Input
                label="Имя КЦ"
                placeholder="Имя сотрудника колл-центра"
                {...register('call_center_name')}
                variant="bordered"
                startContent={<UserIcon className="h-4 w-4 text-gray-400" />}
              />
            </div>

            <div className="space-y-4">
              <Textarea
                label="Описание проблемы"
                placeholder="Опишите проблему или запрос клиента"
                {...register('problem')}
                variant="bordered"
                minRows={3}
                startContent={<DocumentTextIcon className="h-4 w-4 text-gray-400" />}
              />

              <Textarea
                label="Заметка КЦ"
                placeholder="Дополнительные заметки от колл-центра"
                {...register('call_center_notes')}
                variant="bordered"
                minRows={2}
              />
            </div>
          </div>

          {/* Summary Section */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Сводка заявки</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Клиент:</span>
                <p className="font-medium">{watch('client_name') || 'Не указан'}</p>
                <p className="text-gray-600">{watch('client_phone') || 'Телефон не указан'}</p>
              </div>
              <div>
                <span className="text-gray-600">Город:</span>
                <p className="font-medium">
                  {watch('city_id') 
                    ? cities.find(c => c.id === watch('city_id'))?.name || 'Не выбран'
                    : 'Не выбран'
                  }
                </p>
              </div>
              <div>
                <span className="text-gray-600">Тип заявки:</span>
                <p className="font-medium">
                  {watch('request_type_id') 
                    ? requestTypes.find(t => t.id === watch('request_type_id'))?.name || 'Не выбран'
                    : 'Не выбран'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4 pt-6 border-t">
            <Button
              variant="flat"
              onClick={handleCancel}
              disabled={creating}
            >
              Отмена
            </Button>
            <Button
              type="submit"
              color="primary"
              isLoading={creating}
              startContent={!creating ? <ClipboardDocumentListIcon className="h-4 w-4" /> : undefined}
            >
              {creating ? 'Создаю...' : 'Создать заявку'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default IncomingRequestCreatePage; 