import React, { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Input, 
  Button, 
  Select, 
  SelectItem, 
  Card, 
  Textarea, 
  Divider 
} from '@heroui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { 
  ArrowLeftIcon, 
  PlusCircleIcon, 
  BanknotesIcon, 
  CalendarIcon 
} from '@heroicons/react/24/outline';
import dayjs from 'dayjs';
import { transactionsApi, type TransactionCreate } from '../api/transactions';
import { useAuth } from '../contexts/AuthContext';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData } from '../hooks/useApiData';
import { useNotification } from '../contexts/NotificationContext';

const schema = z.object({
  city_id: z.string().min(1, 'Выберите город'),
  transaction_type_id: z.string().min(1, 'Выберите тип дохода'),
  specified_date: z.string().min(1, 'Выберите дату'),
  amount: z.number().min(0.01, 'Сумма должна быть больше 0'),
  payment_reason: z.string().min(1, 'Укажите основание платежа'),
  notes: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

const CashIncomeAddPage: React.FC = () => {
  const { user } = useAuth();
  const { cities } = useAppData();
  const { showSuccess, showError } = useNotification();
  const navigate = useNavigate();

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      specified_date: dayjs().format('YYYY-MM-DD'),
      city_id: ''
    }
  });

  const loadTransactionTypesData = useCallback(async () => {
    const types = await transactionsApi.getTransactionTypes();
    return types.filter(t => t.name.toLowerCase().includes('приход'));
  }, []);

  const { data: transactionTypes = [], loading: typesLoading } = useApiData(loadTransactionTypesData);

  const currentCity = useMemo(() => null, []);

  const onSubmit = useCallback(async (data: FormData) => {
    try {
      const transactionData: TransactionCreate = {
        city_id: Number(data.city_id),
        transaction_type_id: Number(data.transaction_type_id),
        amount: String(Math.abs(data.amount)), // Positive for income
        specified_date: data.specified_date,
        notes: data.notes || '',
      };
      await transactionsApi.createTransaction(transactionData);
      showSuccess('Доход успешно добавлен');
      navigate('/cash/income');
    } catch (error) {
      console.error('Error creating income:', error);
      const errorMessage = (error as { message?: string })?.message || 'Ошибка сохранения';
      showError(errorMessage);
    }
  }, [showSuccess, showError, navigate]);

  const totalAmount = watch('amount') || 0;

  return (
    <div className="max-w-3xl mx-auto px-2 py-10">
      <Card className="rounded-3xl shadow-2xl border-0 bg-white/90 p-10">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="light"
            startContent={<ArrowLeftIcon className="h-5 w-5" />}
            onClick={() => navigate('/cash/income')}
            className="!px-4 !py-2"
          >
            Назад
          </Button>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center rounded-full bg-green-100 text-green-700 mr-2 p-2">
              <BanknotesIcon className="h-7 w-7" />
            </span>
            <h1 className="text-2xl font-bold mb-0">Добавить доход</h1>
          </div>
        </div>
        <Divider className="mb-8" />
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          {/* Секция: Основная информация */}
          <div className="space-y-6">
            <h5 className="text-gray-500 mb-4 flex items-center gap-2 text-lg font-semibold">
              <CalendarIcon className="h-5 w-5" /> Основная информация
            </h5>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Город <span className="text-red-500">*</span>
                </label>
                {false ? (
                  <Input
                    value={currentCity.name}
                    isDisabled
                    size="md"
                    startContent={<span className="text-gray-400">🏢</span>}
                  />
                ) : (
                  <Select
                    placeholder="Выберите город"
                    selectedKeys={watch('city_id') ? [watch('city_id')] : []}
                    onSelectionChange={(keys) => setValue('city_id', Array.from(keys)[0] as string)}
                    isInvalid={!!errors.city_id}
                    errorMessage={errors.city_id?.message}
                    size="md"
                  >
                    {cities.map((city) => (
                      <SelectItem key={city.id}>
                        {city.name}
                      </SelectItem>
                    ))}
                  </Select>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Тип дохода <span className="text-red-500">*</span>
                </label>
                <Select
                  placeholder="Выберите тип"
                  selectedKeys={watch('transaction_type_id') ? [watch('transaction_type_id')] : []}
                  onSelectionChange={(keys) => setValue('transaction_type_id', Array.from(keys)[0] as string)}
                  isInvalid={!!errors.transaction_type_id}
                  errorMessage={errors.transaction_type_id?.message}
                  isLoading={typesLoading}
                  size="md"
                >
                  {(transactionTypes || []).map(type => (
                    <SelectItem key={type.id}>
                      {type.name}
                    </SelectItem>
                  ))}
                </Select>
              </div>

              <Input
                label="Дата"
                type="date"
                {...register('specified_date')}
                isInvalid={!!errors.specified_date}
                errorMessage={errors.specified_date?.message}
                size="md"
                isRequired
                startContent={<CalendarIcon className="h-4 w-4 text-gray-400" />}
              />

              <Input
                label="Сумма"
                type="number"
                step="0.01"
                min="0.01"
                {...register('amount', { valueAsNumber: true })}
                isInvalid={!!errors.amount}
                errorMessage={errors.amount?.message}
                size="md"
                isRequired
                startContent={<span className="text-green-600">₽</span>}
                endContent={
                  totalAmount > 0 && (
                    <span className="text-sm text-green-600 font-medium">
                      {new Intl.NumberFormat('ru-RU', {
                        style: 'currency',
                        currency: 'RUB'
                      }).format(totalAmount)}
                    </span>
                  )
                }
              />
            </div>
          </div>

          <Divider />

          {/* Секция: Детали */}
          <div className="space-y-6">
            <h5 className="text-gray-500 mb-4 flex items-center gap-2 text-lg font-semibold">
              <PlusCircleIcon className="h-5 w-5" /> Детали
            </h5>
            
            <Textarea
              label="Основание платежа"
              {...register('payment_reason')}
              isInvalid={!!errors.payment_reason}
              errorMessage={errors.payment_reason?.message}
              minRows={3}
              size="md"
              isRequired
              placeholder="Укажите основание для получения дохода..."
            />

            <Textarea
              label="Примечание"
              {...register('notes')}
              minRows={2}
              size="md"
              placeholder="Дополнительная информация (необязательно)..."
            />
          </div>

          {/* Сводка */}
          {totalAmount > 0 && (
            <>
              <Divider />
              <div className="bg-green-50 rounded-2xl p-6">
                <h6 className="text-green-800 font-semibold mb-2">Сводка по доходу</h6>
                <div className="text-2xl font-bold text-green-700">
                  +{new Intl.NumberFormat('ru-RU', {
                    style: 'currency',
                    currency: 'RUB'
                  }).format(totalAmount)}
                </div>
                <p className="text-green-600 text-sm mt-1">
                  {currentCity ? `в городе ${currentCity.name}` : ''}
                </p>
              </div>
            </>
          )}

          <div className="flex justify-end gap-4 mt-8">
            <Button
              variant="light"
              size="lg"
              onClick={() => navigate('/cash/income')}
              startContent={<ArrowLeftIcon className="h-5 w-5" />}
            >
              Отмена
            </Button>
            <Button
              type="submit"
              color="success"
              size="lg"
              startContent={<PlusCircleIcon className="h-5 w-5" />}
            >
              Добавить доход
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default CashIncomeAddPage; 