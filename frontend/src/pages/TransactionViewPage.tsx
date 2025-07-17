import React, { useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Input,
  Button,
  Select,
  SelectItem,
  Card,
  Textarea,
  Spinner,
  Chip,
  Divider
} from '@heroui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeftIcon, PencilIcon, CheckIcon, XMarkIcon, BanknotesIcon } from '@heroicons/react/24/outline';
import { transactionsApi } from '../api/transactions';
import type { Transaction, TransactionType } from '../types/api';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData, useMultipleApiData } from '../hooks/useApiData';
import { useNotification } from '../contexts/NotificationContext';
import dayjs from 'dayjs';

interface ExtendedTransaction extends Transaction {
  payment_reason?: string;
}

const schema = z.object({
  city_id: z.number(),
  type_id: z.number(),
  amount: z.number(),
  description: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

const TransactionViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const { cities } = useAppData();
  
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const loadTransactionData = useCallback(async () => {
    const data = await transactionsApi.getTransaction(Number(id));
    
    // Заполняем форму данными транзакции
    reset({
      city_id: data.city.id,
      type_id: data.type.id,
      amount: Math.abs(Number(data.amount)),
      description: data.description || '',
    });
    
    return data;
  }, [id, reset]);

  const loadTransactionTypesData = useCallback(async () => {
    return await transactionsApi.getTransactionTypes();
  }, []);

  const { data: transaction, loading } = useApiData(loadTransactionData);
  const { data: apiData } = useMultipleApiData({
    transactionTypes: loadTransactionTypesData
  });

  const transactionTypes = useMemo(() => 
    Array.isArray(apiData?.transactionTypes) ? apiData.transactionTypes : [], 
    [apiData?.transactionTypes]
  );

  const onSubmit = useCallback(async (data: FormData) => {
    if (!transaction) return;
    
    setSaving(true);
    try {
      const updateData = {
        city_id: data.city_id,
        type_id: data.type_id,
        amount: Number(transaction.amount) < 0 ? -Math.abs(data.amount) : Math.abs(data.amount),
        description: data.description || '',
      };

      await transactionsApi.updateTransaction(transaction.id, updateData);
      setEditing(false);
      showSuccess('Транзакция обновлена');
      // Перезагружаем данные
      reset({
        city_id: transaction.city.id,
        type_id: transaction.type.id,
        amount: Math.abs(Number(transaction.amount)),
        description: transaction.description || '',
      });
    } catch (error) {
      console.error('Error updating transaction:', error);
      showError('Ошибка при обновлении транзакции');
    } finally {
      setSaving(false);
    }
  }, [transaction, showSuccess, showError, reset]);

  const startEditing = useCallback(() => {
    setEditing(true);
  }, []);

  const cancelEditing = useCallback(() => {
    setEditing(false);
    if (transaction) {
      reset({
        city_id: transaction.city.id,
        type_id: transaction.type.id,
        amount: Math.abs(Number(transaction.amount)),
        description: transaction.description || '',
      });
    }
  }, [transaction, reset]);

  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-6">
          <div className="text-center">
            <p className="text-gray-600">Транзакция не найдена</p>
            <Button
              color="primary"
              onClick={() => navigate('/transactions')}
              className="mt-4"
            >
              Вернуться к списку
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-2 py-10">
      <Card className="rounded-3xl shadow-2xl border-0 bg-white/90 p-10">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="light"
            onClick={() => navigate('/transactions')}
            startContent={<ArrowLeftIcon className="h-4 w-4" />}
            className="!px-4 !py-2"
          >
            Назад
          </Button>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center rounded-full bg-blue-100 text-blue-700 mr-2 p-2">
              <BanknotesIcon className="h-7 w-7" />
            </span>
            <h1 className="text-2xl font-bold mb-0">Транзакция #{transaction.id}</h1>
            <Chip color={Number(transaction.amount) >= 0 ? 'success' : 'danger'}>
              {formatCurrency(Number(transaction.amount))}
            </Chip>
          </div>
        </div>
        <Divider className="mb-8" />

        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Информация о транзакции</h2>
            {!editing && (
              <Button
                color="primary"
                onClick={startEditing}
                startContent={<PencilIcon className="h-4 w-4" />}
              >
                Редактировать
              </Button>
            )}
          </div>

          {editing ? (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Select
                  label="Город"
                  selectedKeys={watch('city_id') ? [String(watch('city_id'))] : []}
                  onSelectionChange={(keys) => setValue('city_id', Number(Array.from(keys)[0]))}
                  isInvalid={!!errors.city_id}
                  errorMessage={errors.city_id?.message}
                >
                  {cities.map((city) => (
                    <SelectItem key={city.id}>
                      {city.name}
                    </SelectItem>
                  ))}
                </Select>

                <Select
                  label="Тип транзакции"
                  selectedKeys={watch('type_id') ? [String(watch('type_id'))] : []}
                  onSelectionChange={(keys) => setValue('type_id', Number(Array.from(keys)[0]))}
                  isInvalid={!!errors.type_id}
                  errorMessage={errors.type_id?.message}
                >
                  {transactionTypes.map((type) => (
                    <SelectItem key={type.id}>
                      {type.name}
                    </SelectItem>
                  ))}
                </Select>

                <Input
                  type="number"
                  step="0.01"
                  label="Сумма"
                  {...register('amount', { valueAsNumber: true })}
                  isInvalid={!!errors.amount}
                  errorMessage={errors.amount?.message}
                />

                <Input
                  type="date"
                  label="Дата"
                  {...register('specified_date')}
                  isInvalid={!!errors.specified_date}
                  errorMessage={errors.specified_date?.message}
                />
              </div>

                              <Textarea
                  label="Описание"
                  {...register('description')}
                  isInvalid={!!errors.description}
                  errorMessage={errors.description?.message}
                  minRows={2}
                />

              <div className="flex justify-end gap-3">
                <Button
                  variant="light"
                  onClick={cancelEditing}
                  startContent={<XMarkIcon className="h-4 w-4" />}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  color="primary"
                  isLoading={saving}
                  startContent={<CheckIcon className="h-4 w-4" />}
                >
                  Сохранить
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-500">Город:</span>
                  <p className="text-gray-900">{transaction.city.name}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Тип:</span>
                  <p className="text-gray-900">{transaction.type.name}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Сумма:</span>
                  <p className="text-gray-900">
                    <Chip color={Number(transaction.amount) >= 0 ? 'success' : 'danger'}>
                      {formatCurrency(Number(transaction.amount))}
                    </Chip>
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Дата:</span>
                  <p className="text-gray-900">{dayjs(transaction.created_at).format('DD.MM.YYYY')}</p>
                </div>
              </div>
              
              {transaction.description && (
                <div>
                  <span className="text-sm font-medium text-gray-500">Описание:</span>
                  <p className="text-gray-900">{transaction.description}</p>
                </div>
              )}
            </div>
          )}
        </Card>
      </Card>
    </div>
  );
};

export default TransactionViewPage; 