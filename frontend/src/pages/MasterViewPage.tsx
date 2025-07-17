import React, { useState, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  UserIcon, 
  CheckCircleIcon,
  PhoneIcon,
  IdentificationIcon
} from '@heroicons/react/24/outline';
import { 
  Card, 
  Input, 
  Button, 
  Textarea, 
  Select, 
  SelectItem,
  Divider,
  Badge,
  Spinner
} from '@heroui/react';
import { usersApi, type Master } from '../api/users';
import { useAppData } from '../contexts/AppDataContext';
import { useApiData } from '../hooks/useApiData';
import { useNotification } from '../contexts/NotificationContext';

const MasterViewPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const masterId = parseInt(id || '0');
  const { showSuccess, showError } = useNotification();
  const { cities } = useAppData();

  const [saving, setSaving] = useState(false);

  // Редактируемые поля
  const [editForm, setEditForm] = useState({
    full_name: '',
    phone_number: '',
    birth_date: '',
    passport: '',
    status: 'active',
    chat_id: '',
    city_id: 0,
    notes: ''
  });

  const loadMasterData = useCallback(async () => {
    const masterData = await usersApi.getMaster(masterId);
    
    // Инициализируем форму редактирования
    setEditForm({
      full_name: masterData.full_name || '',
      phone_number: masterData.phone_number || '',
      birth_date: masterData.birth_date || '',
      passport: masterData.passport || '',
      status: masterData.status || 'active',
      chat_id: masterData.chat_id || '',
      city_id: masterData.city_id || 0,
      notes: masterData.notes || ''
    });
    
    return masterData;
  }, [masterId]);

  const { data: master, loading, error } = useApiData(loadMasterData);

  const handleSave = useCallback(async () => {
    try {
      setSaving(true);
      await usersApi.updateMaster(masterId, editForm);
      showSuccess('Данные мастера успешно обновлены');
    } catch (error) {
      console.error('Error updating master:', error);
      showError('Ошибка сохранения данных');
    } finally {
      setSaving(false);
    }
  }, [masterId, editForm, showSuccess, showError]);

  const handleInputChange = useCallback((field: keyof typeof editForm, value: any) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  }, []);

  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  }, []);

  const getStatusBadge = useCallback((status: string) => {
    const statusConfig: Record<string, { label: string, color: "default" | "success" | "warning" | "danger" }> = {
      'active': { label: 'Активен', color: 'success' },
      'inactive': { label: 'Неактивен', color: 'danger' },
      'busy': { label: 'Занят', color: 'warning' }
    };
    const config = statusConfig[status] || { label: status || 'Неизвестно', color: 'default' };
    return <Badge color={config.color}>{config.label}</Badge>;
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  if (error && !master) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-2xl">
          {error || 'Мастер не найден'}
        </Card>
      </div>
    );
  }

  if (!master) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-2 py-10">
      <Card className="rounded-3xl shadow-2xl border-0 bg-white/90 p-10">
        {/* Заголовок */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="light"
            onClick={() => navigate('/masters')}
            startContent={<ArrowLeftIcon className="h-5 w-5" />}
            className="!px-4 !py-2"
          >
            Назад к списку
          </Button>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center rounded-full bg-blue-100 text-blue-700 mr-2 p-2">
              <UserIcon className="h-7 w-7" />
            </span>
            <h1 className="text-2xl font-bold mb-0">Мастер #{master.id}</h1>
            {getStatusBadge(editForm.status)}
          </div>
        </div>
        <Divider className="mb-8" />

        {error && (
          <Card className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-2xl mb-6">
            {error}
          </Card>
        )}

        {/* Основная информация */}
        <div className="space-y-8">
          <div>
            <h5 className="text-gray-500 mb-6 flex items-center gap-2 text-lg font-semibold">
              <IdentificationIcon className="h-5 w-5" /> Персональная информация
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Первая колонка */}
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ID</label>
                  <Input value={String(master.id)} readOnly size="md" />
                </div>
                <Input
                  label="ФИО"
                  value={editForm.full_name}
                  onChange={(e) => handleInputChange('full_name', e.target.value)}
                  size="md"
                />
                <Input
                  label="Телефон"
                  type="tel"
                  value={editForm.phone_number}
                  onChange={(e) => handleInputChange('phone_number', e.target.value)}
                  size="md"
                  startContent={
                    editForm.phone_number ? (
                      <a href={`tel:${editForm.phone_number}`} className="text-blue-600">
                        <PhoneIcon className="h-4 w-4" />
                      </a>
                    ) : (
                      <PhoneIcon className="h-4 w-4 text-gray-400" />
                    )
                  }
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Логин</label>
                  <Input value={master.login || '-'} readOnly size="md" />
                </div>
              </div>

              {/* Вторая колонка */}
              <div className="space-y-6">
                <Select
                  label="Город"
                  selectedKeys={editForm.city_id ? [String(editForm.city_id)] : []}
                  onSelectionChange={(keys) => {
                    const selectedKey = Array.from(keys)[0];
                    handleInputChange('city_id', selectedKey ? Number(selectedKey) : 0);
                  }}
                >
                  {cities.map((city) => (
                    <SelectItem key={city.id}>{city.name}</SelectItem>
                  ))}
                </Select>
                <Select
                  label="Статус"
                  selectedKeys={[editForm.status]}
                  onSelectionChange={(keys) => {
                    const selectedKey = Array.from(keys)[0];
                    handleInputChange('status', selectedKey);
                  }}
                >
                  <SelectItem key="active">Активен</SelectItem>
                  <SelectItem key="inactive">Неактивен</SelectItem>
                  <SelectItem key="busy">Занят</SelectItem>
                </Select>
                <Input
                  label="Дата рождения"
                  type="date"
                  value={editForm.birth_date}
                  onChange={(e) => handleInputChange('birth_date', e.target.value)}
                  size="md"
                />
                <Input
                  label="Паспорт"
                  value={editForm.passport}
                  onChange={(e) => handleInputChange('passport', e.target.value)}
                  size="md"
                />
              </div>

              {/* Третья колонка */}
              <div className="space-y-6">
                <Input
                  label="Chat ID (Telegram)"
                  value={editForm.chat_id}
                  onChange={(e) => handleInputChange('chat_id', e.target.value)}
                  size="md"
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Дата создания</label>
                  <Input 
                    value={master.created_at ? formatDate(master.created_at) : '-'} 
                    readOnly 
                    size="md" 
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Заметки */}
          <div>
            <Textarea
              label="Заметки"
              value={editForm.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              minRows={3}
              size="md"
            />
          </div>

          {/* Кнопки */}
          <div className="flex justify-end gap-4 mt-8">
            <Button
              variant="light"
              size="lg"
              onClick={() => navigate('/masters')}
              startContent={<ArrowLeftIcon className="h-5 w-5" />}
            >
              Назад
            </Button>
            <Button
              color="primary"
              size="lg"
              onClick={handleSave}
              isLoading={saving}
              startContent={<CheckCircleIcon className="h-5 w-5" />}
            >
              Сохранить
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default MasterViewPage; 