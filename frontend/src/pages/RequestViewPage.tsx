import React, { useState, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftIcon, DocumentTextIcon, UserIcon, BanknotesIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { Card, Input, Button, Badge, Divider, Select, SelectItem, Textarea } from '@heroui/react';
import { requestsApi, type Master } from '../api/requests';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData, useMultipleApiData } from '../hooks/useApiData';
import { useNotification } from '../contexts/NotificationContext';

const RequestViewPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const requestId = parseInt(id || '0');
  const { showSuccess, showError } = useNotification();
  
  const { cities, requestTypes, directions } = useAppData();

  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Редактируемые поля
  const [editForm, setEditForm] = useState({
    status: '',
    master_id: 0,
    net_amount: 0,
    expense: 0,
    result: 0
  });

  // --- Загрузка файлов ---
  const [bsoFile, setBsoFile] = useState<File | null>(null);
  const [expenseFile, setExpenseFile] = useState<File | null>(null);
  const [recordingFile, setRecordingFile] = useState<File | null>(null);

  const loadRequestData = useCallback(async () => {
    const requestData = await requestsApi.getRequest(requestId);
    console.log(`🔍 Загружены данные заявки ${requestId}:`, {
      apiStatus: requestData.status,
      allData: requestData
    });
    setEditForm({
      status: requestData.status || 'waiting',
      master_id: Number(requestData.master_id) || 0,
      net_amount: Number(requestData.net_amount) || 0,
      expense: Number(requestData.expenses) || 0,
      result: Number(requestData.result) || 0
    });
    console.log(`📝 Установлен editForm статус:`, requestData.status || 'waiting');
    return requestData;
  }, [requestId]);

  const loadMastersData = useCallback(async () => {
    return await requestsApi.getMasters();
  }, []);

  const loadAdvertisingCampaignsData = useCallback(async () => {
    const { advertisingCampaignsApi } = await import('../api/advertisingCampaigns');
    return await advertisingCampaignsApi.getAdvertisingCampaigns();
  }, []);

  const { data: request, loading, error, refetch: refetchRequest } = useApiData(loadRequestData);
  const { 
    data: apiData, 
    loading: multiLoading, 
    error: multiError 
  } = useMultipleApiData({
    masters: loadMastersData,
    advertisingCampaigns: loadAdvertisingCampaignsData
  });

  const masters = useMemo(() => Array.isArray(apiData?.masters) ? apiData.masters : [], [apiData?.masters]);
  const advertisingCampaigns = useMemo(() => Array.isArray(apiData?.advertisingCampaigns) ? apiData.advertisingCampaigns : [], [apiData?.advertisingCampaigns]);

  // Автоматический пересчёт
  const result = Number(editForm.result);
  const expenses = Number(editForm.expense);
  const netAmount = result - expenses;
  const masterHandover = netAmount / 2;

  const handleSave = useCallback(async () => {
    try {
      setSaving(true);
      console.log(`💾 Начинается сохранение заявки ${requestId} со статусом:`, editForm.status);
      const updateData = {
        status: editForm.status as any,
        master_id: editForm.master_id || undefined,
        net_amount: editForm.net_amount,
        expenses: editForm.expense,
        result: String(editForm.result),
        master_handover: masterHandover,
      };
      console.log(`📤 Отправляемые данные:`, updateData);
      
      const savedData = await requestsApi.updateRequest(requestId, updateData);
      console.log(`✅ Ответ от сервера:`, savedData);
      
      // После успешного сохранения — загружаем файлы, если выбраны
      setUploading(true);
      if (bsoFile) await requestsApi.uploadBso(requestId, bsoFile);
      if (expenseFile) await requestsApi.uploadExpense(requestId, expenseFile);
      if (recordingFile) await requestsApi.uploadRecording(requestId, recordingFile);
      
      setBsoFile(null);
      setExpenseFile(null);
      setRecordingFile(null);
      
      showSuccess('Данные успешно сохранены');
      
      console.log(`🔄 Начинается перезагрузка данных заявки ${requestId}`);
      
      // Небольшая задержка чтобы сервер успел зафиксировать изменения
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Принудительная перезагрузка данных без кеша
      await refetchRequest();
      console.log(`✅ Данные заявки ${requestId} перезагружены`);
    } catch (error) {
      console.error('Error saving request:', error);
      showError('Ошибка сохранения данных');
    } finally {
      setSaving(false);
      setUploading(false);
    }
  }, [requestId, editForm, bsoFile, expenseFile, recordingFile, showSuccess, showError, refetchRequest, masterHandover]);

  const handleInputChange = useCallback((field: keyof typeof editForm, value: any) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  }, []);

  const getCityName = useCallback((cityId: number) => 
    cities.find(c => c.id === cityId)?.name || '-', [cities]);
  
  const getRequestTypeName = useCallback((typeId: number) => 
    requestTypes.find(t => t.id === typeId)?.name || '-', [requestTypes]);
  
  const getDirectionName = useCallback((directionId?: number) => 
    directionId ? (directions.find(d => d.id === directionId)?.name || '-') : '-', [directions]);
  
  const getAdvertisingCampaignName = useCallback((campaignId?: number) => {
    if (!campaignId) return '-';
    const campaign = advertisingCampaigns.find(c => c.id === campaignId);
    return campaign?.name || '-';
  }, [advertisingCampaigns]);

  const getStatusBadge = useCallback((status: string) => {
    const statusConfig: Record<string, { label: string, color: "default" | "warning" | "primary" | "secondary" | "success" | "danger" }> = {
      'waiting': { label: 'Ожидает', color: 'warning' },
      'waiting_acceptance': { label: 'Ожидает принятия', color: 'warning' },
      'accepted': { label: 'Принял', color: 'primary' },
      'in_way': { label: 'В пути', color: 'secondary' },
      'in_work': { label: 'В работе', color: 'secondary' },
      'done': { label: 'Готово', color: 'success' },
      'refused': { label: 'Отказ', color: 'danger' },
      'modern': { label: 'Модерн', color: 'secondary' },
      'no_order': { label: 'НеЗаказ', color: 'default' }
    };
    const config = statusConfig[status] || { label: status || 'Неизвестно', color: 'default' };
    return <Badge color={config.color}>{config.label}</Badge>;
  }, []);

  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  }, []);

  const formatCurrency = useCallback((amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  }, []);

  if (loading || multiLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if ((error || multiError) && !request) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-2xl">
          {error || multiError || 'Заявка не найдена'}
        </Card>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-2 py-10">
      <Card className="rounded-3xl shadow-2xl border-0 bg-white/90 p-10">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="light"
            startContent={<ArrowLeftIcon className="h-5 w-5" />}
            onClick={() => navigate('/requests')}
            className="!px-4 !py-2"
          >
            Назад
          </Button>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center rounded-full bg-green-100 text-green-700 mr-2 p-2">
              <DocumentTextIcon className="h-7 w-7" />
            </span>
            <h2 className="text-2xl font-bold mb-0">Заявка #{request.id}</h2>
            {getStatusBadge(editForm.status)}
          </div>
        </div>
        <Divider className="mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {/* Секция: Клиент и детали */}
          <div className="space-y-6">
            <h5 className="text-gray-500 mb-2 flex items-center gap-2 text-lg font-semibold">
              <UserIcon className="h-5 w-5" /> Клиент
            </h5>
            <Input label="Имя клиента" value={request.client_name} readOnly fullWidth size="md" />
            <Input 
              label="Телефон" 
              value={request.client_phone} 
              readOnly 
              fullWidth 
              size="md"
              startContent={
                <a href={`tel:${request.client_phone}`} className="text-blue-600">
                  📞
                </a>
              }
            />
            <Input label="Город" value={getCityName(request.city_id)} readOnly fullWidth size="md" />
            <Input label="Адрес" value={request.address || '-'} readOnly fullWidth size="md" />
            <Textarea label="Проблема" value={request.problem || ''} readOnly fullWidth size="md" minRows={2} />
            
            {/* --- Загрузка файлов к заявке --- */}
            <div className="space-y-4 mt-8">
              <h5 className="text-gray-500 mb-2 flex items-center gap-2 text-lg font-semibold">Файлы по заявке</h5>
              {/* БСО */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">БСО</label>
                {request.bso_file_path ? (
                  <div className="flex flex-col gap-2">
                    {/\.(jpg|jpeg|png)$/i.test(request.bso_file_path) ? (
                      <a href={`/${request.bso_file_path.replaceAll('\\', '/')}`} target="_blank" rel="noopener noreferrer">
                        <img src={`/${request.bso_file_path.replaceAll('\\', '/')}`} alt="БСО" className="max-h-40 rounded border" />
                      </a>
                    ) :
                    /\.pdf$/i.test(request.bso_file_path) ? (
                      <iframe src={`/${request.bso_file_path.replaceAll('\\', '/')}`} title="БСО PDF" className="w-full h-40 border rounded" />
                    ) : (
                      <a href={`/${request.bso_file_path.replaceAll('\\', '/')}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Скачать БСО</a>
                    )}
                  </div>
                ) : (
                  <input type="file" accept=".jpg,.jpeg,.png,.pdf,.doc,.docx" disabled={uploading || saving} onChange={e => e.target.files && setBsoFile(e.target.files[0])} />
                )}
                {bsoFile && <span className="ml-2 text-xs text-gray-500">{bsoFile.name}</span>}
              </div>
              {/* Чек расхода */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Чек расхода</label>
                {request.expense_file_path ? (
                  <div className="flex flex-col gap-2">
                    {/\.(jpg|jpeg|png)$/i.test(request.expense_file_path) ? (
                      <a href={`/${request.expense_file_path.replaceAll('\\', '/')}`} target="_blank" rel="noopener noreferrer">
                        <img src={`/${request.expense_file_path.replaceAll('\\', '/')}`} alt="Чек расхода" className="max-h-40 rounded border" />
                      </a>
                    ) :
                    /\.pdf$/i.test(request.expense_file_path) ? (
                      <iframe src={`/${request.expense_file_path.replaceAll('\\', '/')}`} title="Чек PDF" className="w-full h-40 border rounded" />
                    ) : (
                      <a href={`/${request.expense_file_path.replaceAll('\\', '/')}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Скачать чек</a>
                    )}
                  </div>
                ) : (
                  <input type="file" accept=".jpg,.jpeg,.png,.pdf,.doc,.docx" disabled={uploading || saving} onChange={e => e.target.files && setExpenseFile(e.target.files[0])} />
                )}
                {expenseFile && <span className="ml-2 text-xs text-gray-500">{expenseFile.name}</span>}
              </div>
              {/* Аудиозапись */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Аудиозапись</label>
                {request.recording_file_path ? (
                  <div className="flex flex-col gap-2">
                    {/\.(mp3|wav|ogg|m4a|amr)$/i.test(request.recording_file_path) ? (
                      <audio controls src={`/${request.recording_file_path.replaceAll('\\', '/')}`} className="w-full">
                        Ваш браузер не поддерживает аудио.
                      </audio>
                    ) : (
                      <a href={`/${request.recording_file_path.replaceAll('\\', '/')}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Скачать аудио</a>
                    )}
                  </div>
                ) : (
                  <input type="file" accept=".mp3,.wav,.ogg,.m4a,.amr" disabled={uploading || saving} onChange={e => e.target.files && setRecordingFile(e.target.files[0])} />
                )}
                {recordingFile && <span className="ml-2 text-xs text-gray-500">{recordingFile.name}</span>}
              </div>
            </div>
          </div>
          
          {/* Секция: Детали заявки */}
          <div className="space-y-6">
            <h5 className="text-gray-500 mb-2 flex items-center gap-2 text-lg font-semibold">
              <CheckCircleIcon className="h-5 w-5" /> Детали
            </h5>
            <Input label="РК" value={getAdvertisingCampaignName(request.advertising_campaign_id)} readOnly fullWidth size="md" />
            <Input label="Тип заявки" value={getRequestTypeName(request.request_type_id)} readOnly fullWidth size="md" />
            <Input label="Дата встречи" value={request.meeting_date ? formatDate(request.meeting_date) : '-'} readOnly fullWidth size="md" />
            <Input label="Направление" value={getDirectionName(request.direction_id)} readOnly fullWidth size="md" />
            
            <Select
              label="Статус"
              selectedKeys={editForm.status ? [editForm.status] : []}
              onSelectionChange={(keys) => {
                const selectedKey = Array.from(keys)[0];
                handleInputChange('status', selectedKey);
              }}
            >
              <SelectItem key="Новая">Новая</SelectItem>
              <SelectItem key="Ожидает">Ожидает</SelectItem>
              <SelectItem key="Ожидает Принятия">Ожидает Принятия</SelectItem>
              <SelectItem key="Принял">Принял</SelectItem>
              <SelectItem key="В пути">В пути</SelectItem>
              <SelectItem key="В работе">В работе</SelectItem>
              <SelectItem key="Модерн">Модерн</SelectItem>
              <SelectItem key="Готово">Готово</SelectItem>
              <SelectItem key="Отказ">Отказ</SelectItem>
              <SelectItem key="Перезвонить">Перезвонить</SelectItem>
              <SelectItem key="ТНО">ТНО</SelectItem>
            </Select>
            
            <Select
              label="Мастер"
              selectedKeys={editForm.master_id ? [String(editForm.master_id)] : []}
              onSelectionChange={(keys) => {
                const selectedKey = Array.from(keys)[0];
                handleInputChange('master_id', selectedKey ? Number(selectedKey) : 0);
              }}
            >
              <SelectItem key="0">Не назначен</SelectItem>
              {(masters || []).map((master: Master) => (
                <SelectItem key={String(master.id)}>{master.full_name}</SelectItem>
              ))}
            </Select>
          </div>
        </div>
        <Divider className="my-10" />
        
        {/* Секция: Финансы */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-8">
          <div className="space-y-6">
            <h5 className="text-gray-500 mb-2 flex items-center gap-2 text-lg font-semibold">
              <BanknotesIcon className="h-5 w-5" /> Финансы
            </h5>
            <Input
              label="Итог"
              value={String(editForm.result)}
              onChange={e => handleInputChange('result', Number(e.target.value))}
              fullWidth
              size="md"
              type="number"
            />
            <Input
              label="Расход"
              value={String(editForm.expense)}
              onChange={e => handleInputChange('expense', Number(e.target.value))}
              fullWidth
              size="md"
              type="number"
            />
          </div>
          <div className="flex flex-col justify-center items-start gap-6">
            <div>
              <span className="text-gray-500 text-sm">Чистыми</span>
              <div className="text-2xl font-bold text-green-700 mt-1">{formatCurrency(netAmount)}</div>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Сдача мастера</span>
              <div className="text-2xl font-bold text-blue-700 mt-1">{formatCurrency(masterHandover)}</div>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-4 mt-8">
          <Button variant="light" size="lg" startContent={<ArrowLeftIcon className="h-5 w-5" />} onClick={() => navigate(-1)}>
            Назад
          </Button>
          <Button color="primary" size="lg" isLoading={saving || uploading} onClick={handleSave} startContent={<CheckCircleIcon className="h-5 w-5" />}>
            Сохранить
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default RequestViewPage; 