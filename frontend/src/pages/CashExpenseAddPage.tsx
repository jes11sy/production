import React, { useCallback, useState } from 'react';
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
  MinusCircleIcon, 
  BanknotesIcon, 
  CalendarIcon,
  ArrowUpTrayIcon 
} from '@heroicons/react/24/outline';
import dayjs from 'dayjs';
import { transactionsApi, type TransactionCreate } from '../api/transactions';
import { useAuth } from '../contexts/AuthContext';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData } from '../hooks/useApiData';
import { useNotification } from '../contexts/NotificationContext';

const schema = z.object({
  city_id: z.string().min(1, 'Выберите город'),
  transaction_type_id: z.string().min(1, 'Выберите тип расхода'),
  specified_date: z.string().min(1, 'Выберите дату'),
  amount: z.number().min(0.01, 'Сумма должна быть больше 0'),
  payment_reason: z.string().min(1, 'Укажите основание платежа'),
  notes: z.string().optional(),
  file: z.instanceof(File).optional(),
});

type FormData = z.infer<typeof schema>;

const CashExpenseAddPage: React.FC = () => {
  const { user } = useAuth();
  const { cities } = useAppData();
  const { showSuccess, showError } = useNotification();
  const navigate = useNavigate();
  const [fileList, setFileList] = useState<File[]>([]);

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      specified_date: dayjs().format('YYYY-MM-DD'),
    }
  });

  const loadTransactionTypesData = useCallback(async () => {
    const types = await transactionsApi.getTransactionTypes();
    return types.filter(t => t.name.toLowerCase().includes('расход'));
      }, [setValue]);

  const { data: transactionTypes = [], loading: typesLoading } = useApiData(loadTransactionTypesData);

  const onSubmit = useCallback(async (data: FormData) => {
    try {
      // Create transaction first
      const transactionData: TransactionCreate = {
        city_id: Number(data.city_id),
        transaction_type_id: Number(data.transaction_type_id),
        amount: String(-Math.abs(data.amount)), // Negative for expense
        specified_date: data.specified_date,
        notes: data.notes || '',
      };
      
      const createdTransaction = await transactionsApi.createTransaction(transactionData) as any;
      
      // Upload file if provided
      if (data.file) {
        try {
          await transactionsApi.uploadFile(createdTransaction.id, data.file);
          showSuccess('Расход и файл успешно добавлены');
        } catch (fileError) {
          console.error('Error uploading file:', fileError);
          showSuccess('Расход добавлен, но файл не удалось загрузить');
        }
      } else {
        showSuccess('Расход успешно добавлен');
      }
      
      navigate('/cash/expense');
    } catch (error) {
      console.error('Error creating expense:', error);
      const errorMessage = (error as { message?: string })?.message || 'Ошибка сохранения';
      showError(errorMessage);
    }
  }, [showSuccess, showError, navigate]);

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setFileList([file]);
      setValue('file', file);
    }
  }, []);

  const removeFile = useCallback(() => {
    setFileList([]);
  }, []);

  const totalAmount = watch('amount') || 0;

  return (
    <div className="max-w-3xl mx-auto px-2 py-10">
      <Card className="rounded-3xl shadow-2xl border-0 bg-white/90 p-10">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="light"
            startContent={<ArrowLeftIcon className="h-5 w-5" />}
            onClick={() => navigate('/cash/expense')}
            className="!px-4 !py-2"
          >
            Назад
          </Button>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center rounded-full bg-red-100 text-red-700 mr-2 p-2">
              <BanknotesIcon className="h-7 w-7" />
            </span>
            <h1 className="text-2xl font-bold mb-0">Добавить расход</h1>
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
              <Select
                label="Город"
                placeholder="Выберите город"
                selectedKeys={watch('city_id') ? [watch('city_id')] : []}
                onSelectionChange={(keys) => setValue('city_id', Array.from(keys)[0] as string)}
                isInvalid={!!errors.city_id}
                errorMessage={errors.city_id?.message}
                size="md"
                isRequired
              >
                {cities.map((city) => (
                  <SelectItem key={city.id}>
                    {city.name}
                  </SelectItem>
                ))}
              </Select>

              <Select
                label="Тип расхода"
                placeholder="Выберите тип"
                selectedKeys={watch('transaction_type_id') ? [watch('transaction_type_id')] : []}
                onSelectionChange={(keys) => setValue('transaction_type_id', Array.from(keys)[0] as string)}
                isInvalid={!!errors.transaction_type_id}
                errorMessage={errors.transaction_type_id?.message}
                isLoading={typesLoading}
                size="md"
                isRequired
              >
                {(transactionTypes || []).map(type => (
                  <SelectItem key={type.id}>
                    {type.name}
                  </SelectItem>
                ))}
              </Select>

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
                startContent={<span className="text-red-600">₽</span>}
                endContent={
                  totalAmount > 0 && (
                    <span className="text-sm text-red-600 font-medium">
                      -{new Intl.NumberFormat('ru-RU', {
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
              <MinusCircleIcon className="h-5 w-5" /> Детали
            </h5>
            
            <Textarea
              label="Основание платежа"
              {...register('payment_reason')}
              isInvalid={!!errors.payment_reason}
              errorMessage={errors.payment_reason?.message}
              minRows={3}
              size="md"
              isRequired
              placeholder="Укажите основание для расхода..."
            />

            <Textarea
              label="Примечание"
              {...register('notes')}
              minRows={2}
              size="md"
              placeholder="Дополнительная информация (необязательно)..."
            />

            {/* Загрузка файлов */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Чек или документ
              </label>
              <div className="space-y-2">
                <div className="flex items-center justify-center w-full">
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <ArrowUpTrayIcon className="w-8 h-8 mb-4 text-gray-500" />
                      <p className="mb-2 text-sm text-gray-500">
                        <span className="font-semibold">Нажмите для загрузки</span> или перетащите файл
                      </p>
                      <p className="text-xs text-gray-500">PNG, JPG, PDF (MAX. 10MB)</p>
                    </div>
                    <input
                      type="file"
                      className="hidden"
                      accept=".png,.jpg,.jpeg,.pdf"
                      onChange={handleFileChange}
                    />
                  </label>
                </div>
                {fileList.length > 0 && (
                  <div className="flex items-center justify-between p-2 bg-gray-100 rounded">
                    <span className="text-sm text-gray-700">{fileList[0].name}</span>
                    <Button
                      size="sm"
                      color="danger"
                      variant="light"
                      onClick={removeFile}
                    >
                      Удалить
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Сводка */}
          {totalAmount > 0 && (
            <>
              <Divider />
              <div className="bg-red-50 rounded-2xl p-6">
                <h6 className="text-red-800 font-semibold mb-2">Сводка по расходу</h6>
                <div className="text-2xl font-bold text-red-700">
                  -{new Intl.NumberFormat('ru-RU', {
                    style: 'currency',
                    currency: 'RUB'
                  }).format(totalAmount)}
                </div>
                {fileList.length > 0 && (
                  <p className="text-red-600 text-sm mt-1">
                    📎 Прикреплен документ: {fileList[0].name}
                  </p>
                )}
              </div>
            </>
          )}

          <div className="flex justify-end gap-4 mt-8">
            <Button
              variant="light"
              size="lg"
              onClick={() => navigate('/cash/expense')}
              startContent={<ArrowLeftIcon className="h-5 w-5" />}
            >
              Отмена
            </Button>
            <Button
              type="submit"
              color="danger"
              size="lg"
              startContent={<MinusCircleIcon className="h-5 w-5" />}
            >
              Добавить расход
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default CashExpenseAddPage; 