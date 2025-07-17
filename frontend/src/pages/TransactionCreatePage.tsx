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
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { 
  ArrowLeftIcon, 
  CheckIcon, 
  CurrencyDollarIcon,
  CalendarIcon,
  DocumentTextIcon,
  BuildingOfficeIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { useAppData } from '../contexts/AppDataContext';
import { useNotification } from '../contexts/NotificationContext';
import { transactionsApi } from '../api/transactions';
import type { CreateTransactionData } from '../types/api';
import dayjs from 'dayjs';

const schema = z.object({
  city_id: z.string().min(1, 'Выберите город'),
  type_id: z.string().min(1, 'Выберите тип транзакции'),
  amount: z.number().min(0.01, 'Сумма должна быть больше 0'),
  description: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

const TransactionCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { cities, transactionTypes } = useAppData();
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      description: '',
    }
  });

  const handleCancel = useCallback(() => {
    navigate('/transactions');
  }, [navigate]);

  const onSubmit = useCallback(async (data: FormData) => {
    setLoading(true);
    try {
      const transactionData: CreateTransactionData = {
        city_id: Number(data.city_id),
        type_id: Number(data.type_id),
        amount: data.amount,
        description: data.description || '',
      };

      await transactionsApi.createTransaction(transactionData);
      showSuccess('Транзакция создана успешно');
      navigate('/transactions');
    } catch (error) {
      console.error('Error creating transaction:', error);
      showError('Ошибка при создании транзакции');
    } finally {
      setLoading(false);
    }
  }, [showSuccess, showError, navigate]);

  const handleCityChange = useCallback((keys: any) => {
    const cityId = Array.from(keys)[0] as string;
    setValue('city_id', cityId);
  }, [setValue]);

  const handleTypeChange = useCallback((keys: any) => {
    const typeId = Array.from(keys)[0] as string;
    setValue('type_id', typeId);
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
          <div className="flex items-center justify-center rounded-full bg-green-100 text-green-700 p-3">
            <CurrencyDollarIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Новая транзакция</h1>
            <p className="text-gray-600">Создание новой финансовой транзакции</p>
          </div>
        </div>
      </div>

      {/* Form */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <CurrencyDollarIcon className="h-6 w-6 text-gray-600" />
          <h2 className="text-xl font-semibold">Информация о транзакции</h2>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <div>
                <Select
                  label="Город"
                  placeholder="Выберите город"
                  selectedKeys={watch('city_id') ? [watch('city_id')] : []}
                  onSelectionChange={handleCityChange}
                  isInvalid={!!errors.city_id}
                  errorMessage={errors.city_id?.message}
                  variant="bordered"
                  isRequired
                  startContent={<BuildingOfficeIcon className="h-4 w-4 text-gray-400" />}
                >
                  {cities.map((city) => (
                    <SelectItem key={city.id.toString()}>
                      {city.name}
                    </SelectItem>
                  ))}
                </Select>
              </div>

              <div>
                <Select
                  label="Тип транзакции"
                  placeholder="Выберите тип транзакции"
                  selectedKeys={watch('type_id') ? [watch('type_id')] : []}
                  onSelectionChange={handleTypeChange}
                  isInvalid={!!errors.type_id}
                  errorMessage={errors.type_id?.message}
                  variant="bordered"
                  isRequired
                  startContent={<TagIcon className="h-4 w-4 text-gray-400" />}
                >
                  {transactionTypes.map((type) => (
                    <SelectItem key={type.id.toString()}>
                      {type.name}
                    </SelectItem>
                  ))}
                </Select>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <div>
                <Input
                  label="Сумма"
                  placeholder="Введите сумму"
                  type="number"
                  step="0.01"
                  min="0.01"
                  {...register('amount', { valueAsNumber: true })}
                  isInvalid={!!errors.amount}
                  errorMessage={errors.amount?.message}
                  variant="bordered"
                  isRequired
                  startContent={<CurrencyDollarIcon className="h-4 w-4 text-gray-400" />}
                  endContent={
                    <div className="pointer-events-none flex items-center">
                      <span className="text-default-400 text-small">₽</span>
                    </div>
                  }
                />
              </div>

              <div>
                <Textarea
                  label="Описание"
                  placeholder="Введите описание транзакции"
                  {...register('description')}
                  variant="bordered"
                  minRows={3}
                  startContent={<DocumentTextIcon className="h-4 w-4 text-gray-400" />}
                />
              </div>
            </div>
          </div>

          {/* Summary Section */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Сводка транзакции</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Город:</span>
                <p className="font-medium">
                  {watch('city_id') 
                    ? cities.find(c => c.id.toString() === watch('city_id'))?.name || 'Не выбран'
                    : 'Не выбран'
                  }
                </p>
              </div>
              <div>
                <span className="text-gray-600">Тип:</span>
                <p className="font-medium">
                  {watch('type_id') 
                    ? transactionTypes.find(t => t.id.toString() === watch('type_id'))?.name || 'Не выбран'
                    : 'Не выбран'
                  }
                </p>
              </div>
              <div>
                <span className="text-gray-600">Сумма:</span>
                <p className="font-medium text-green-600">
                  {watch('amount') 
                    ? new Intl.NumberFormat('ru-RU', { 
                        style: 'currency', 
                        currency: 'RUB' 
                      }).format(watch('amount'))
                    : '0 ₽'
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
              disabled={loading}
            >
              Отмена
            </Button>
            <Button
              type="submit"
              color="primary"
              isLoading={loading}
              startContent={!loading ? <CheckIcon className="h-4 w-4" /> : undefined}
            >
              {loading ? 'Создаю...' : 'Создать транзакцию'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default TransactionCreatePage; 