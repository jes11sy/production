import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Input,
  Select,
  SelectItem,
  Textarea
} from '@heroui/react';
import { 
  ArrowLeftIcon,
  UserPlusIcon,
  UserIcon,
  PhoneIcon,
  IdentificationIcon,
  CalendarIcon,
  BuildingOfficeIcon,
  KeyIcon,
  ChatBubbleBottomCenterTextIcon
} from '@heroicons/react/24/outline';
import { useAppData } from '../contexts/AppDataContext';
import { useNotification } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import { usersApi } from '../api/users';

interface CreateMasterRequest {
  city_id: number;
  full_name: string;
  phone_number: string;
  birth_date: string;
  passport: string;
  status: string;
  chat_id: string;
  login: string;
  password: string;
  notes: string;
}

const MasterCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { cities } = useAppData();
  const { showSuccess, showError } = useNotification();

  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<CreateMasterRequest>({
    city_id: 0,
    full_name: '',
    phone_number: '',
    birth_date: '',
    passport: '',
    status: 'active',
    chat_id: '',
    login: '',
    password: '',
    notes: ''
  });

  // Set city for director users
  useEffect(() => {
    if (user?.role === 'director' && user.city_id) {
      setForm((prev: CreateMasterRequest) => ({ ...prev, city_id: user.city_id! }));
    }
  }, [user?.role, user?.city_id]);

  // Memoized handlers
  const handleInputChange = useCallback((field: keyof CreateMasterRequest, value: string | number) => {
    setForm((prev: CreateMasterRequest) => ({ ...prev, [field]: value }));
  }, []);

  const handleFullNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('full_name', e.target.value);
  }, [handleInputChange]);

  const handlePhoneChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('phone_number', e.target.value);
  }, [handleInputChange]);

  const handleBirthDateChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('birth_date', e.target.value);
  }, [handleInputChange]);

  const handlePassportChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('passport', e.target.value);
  }, [handleInputChange]);

  const handleChatIdChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('chat_id', e.target.value);
  }, [handleInputChange]);

  const handleLoginChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('login', e.target.value);
  }, [handleInputChange]);

  const handlePasswordChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('password', e.target.value);
  }, [handleInputChange]);

  const handleNotesChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('notes', e.target.value);
  }, [handleInputChange]);

  const handleCityChange = useCallback((keys: any) => {
    const cityId = Array.from(keys)[0] as string;
    handleInputChange('city_id', parseInt(cityId) || 0);
  }, [handleInputChange]);

  const handleStatusChange = useCallback((keys: any) => {
    const status = Array.from(keys)[0] as string;
    handleInputChange('status', status);
  }, [handleInputChange]);

  const generateCredentials = useCallback(() => {
    let login = '';
    if (form.full_name) {
      const names = form.full_name.toLowerCase().split(' ');
      if (names.length >= 2) {
        login = `${names[0]}.${names[1]}`;
      } else {
        login = names[0];
      }
    }

    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let password = '';
    for (let i = 0; i < 8; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length));
    }

    setForm((prev: CreateMasterRequest) => ({
      ...prev,
      login: login,
      password: password
    }));

    showSuccess('Логин и пароль сгенерированы');
  }, [form.full_name, showSuccess]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!form.city_id || !form.full_name || !form.phone_number || !form.login || !form.password) {
      showError('Пожалуйста, заполните все обязательные поля');
      return;
    }

    try {
      setSaving(true);
      await usersApi.createMaster(form);
      showSuccess('Мастер успешно создан');
      navigate('/masters');
    } catch (error) {
      console.error('Error creating master:', error);
      showError('Ошибка создания мастера');
    } finally {
      setSaving(false);
    }
  }, [form, showError, showSuccess, navigate]);

  const handleCancel = useCallback(() => {
    navigate('/masters');
  }, [navigate]);

  // Get current city name for director
  const currentCityName = user?.role === 'director' && user.city_id 
    ? cities.find(c => c.id === user.city_id)?.name || '' 
    : '';

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
          <div className="flex items-center justify-center rounded-full bg-purple-100 text-purple-700 p-3">
            <UserPlusIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Новый мастер</h1>
            <p className="text-gray-600">Создание нового мастера</p>
          </div>
        </div>
      </div>

      {/* Form */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <UserIcon className="h-6 w-6 text-gray-600" />
          <h2 className="text-xl font-semibold">Информация о мастере</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <Input
                label="ФИО"
                placeholder="Введите полное имя"
                value={form.full_name}
                onChange={handleFullNameChange}
                variant="bordered"
                isRequired
                startContent={<UserIcon className="h-4 w-4 text-gray-400" />}
              />

              <Input
                label="Телефон"
                placeholder="+7 (999) 123-45-67"
                type="tel"
                value={form.phone_number}
                onChange={handlePhoneChange}
                variant="bordered"
                isRequired
                startContent={<PhoneIcon className="h-4 w-4 text-gray-400" />}
              />

              <Input
                label="Дата рождения"
                type="date"
                value={form.birth_date}
                onChange={handleBirthDateChange}
                variant="bordered"
                startContent={<CalendarIcon className="h-4 w-4 text-gray-400" />}
              />

              <Input
                label="Паспорт"
                placeholder="Серия и номер паспорта"
                value={form.passport}
                onChange={handlePassportChange}
                variant="bordered"
                startContent={<IdentificationIcon className="h-4 w-4 text-gray-400" />}
              />

              <Input
                label="Chat ID (Telegram)"
                placeholder="Telegram Chat ID"
                value={form.chat_id}
                onChange={handleChatIdChange}
                variant="bordered"
                startContent={<ChatBubbleBottomCenterTextIcon className="h-4 w-4 text-gray-400" />}
              />
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              {user?.role === 'director' ? (
                <Input
                  label="Город"
                  value={currentCityName}
                  variant="bordered"
                  isDisabled
                  startContent={<BuildingOfficeIcon className="h-4 w-4 text-gray-400" />}
                />
              ) : (
                <Select
                  label="Город"
                  placeholder="Выберите город"
                  selectedKeys={form.city_id ? [form.city_id.toString()] : []}
                  onSelectionChange={handleCityChange}
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
              )}

              <Select
                label="Статус"
                placeholder="Выберите статус"
                selectedKeys={[form.status]}
                onSelectionChange={handleStatusChange}
                variant="bordered"
              >
                <SelectItem key="active">Активен</SelectItem>
                <SelectItem key="inactive">Неактивен</SelectItem>
                <SelectItem key="busy">Занят</SelectItem>
              </Select>

              <Input
                label="Логин"
                placeholder="Введите логин"
                value={form.login}
                onChange={handleLoginChange}
                variant="bordered"
                isRequired
                startContent={<UserIcon className="h-4 w-4 text-gray-400" />}
              />

              <div className="space-y-2">
                <Input
                  label="Пароль"
                  placeholder="Введите пароль"
                  value={form.password}
                  onChange={handlePasswordChange}
                  variant="bordered"
                  isRequired
                  startContent={<KeyIcon className="h-4 w-4 text-gray-400" />}
                  endContent={
                    <Button
                      size="sm"
                      variant="flat"
                      color="success"
                      onClick={generateCredentials}
                      className="min-w-unit-20"
                    >
                      Сгенерировать
                    </Button>
                  }
                />
              </div>

              <Textarea
                label="Заметки"
                placeholder="Дополнительная информация"
                value={form.notes}
                onChange={handleNotesChange}
                variant="bordered"
                minRows={3}
              />
            </div>
          </div>

          {/* Master Summary */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Сводка мастера</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600">ФИО:</span>
                <p className="font-medium">{form.full_name || 'Не указано'}</p>
              </div>
              <div>
                <span className="text-gray-600">Телефон:</span>
                <p className="font-medium">{form.phone_number || 'Не указан'}</p>
              </div>
              <div>
                <span className="text-gray-600">Город:</span>
                <p className="font-medium">
                  {user?.role === 'director' 
                    ? currentCityName
                    : form.city_id 
                      ? cities.find(c => c.id === form.city_id)?.name || 'Не выбран'
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
              disabled={saving}
            >
              Отмена
            </Button>
            <Button
              color="primary"
              type="submit"
              isLoading={saving}
              startContent={!saving ? <UserPlusIcon className="h-4 w-4" /> : undefined}
            >
              {saving ? 'Создаю...' : 'Создать мастера'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default MasterCreatePage; 