import React, { useState, useCallback } from 'react';
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
  KeyIcon,
  UserIcon,
  BuildingOfficeIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { useAppData } from '../contexts/AppDataContext';
import { useNotification } from '../contexts/NotificationContext';
import { usersApi } from '../api/users';

interface EmployeeForm {
  city_id: number;
  role_id: number;
  name: string;
  status: string;
  login: string;
  password: string;
  notes: string;
}

const EmployeeCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { cities, roles } = useAppData();
  const { showSuccess, showError } = useNotification();

  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<EmployeeForm>({
    city_id: 0,
    role_id: 0,
    name: '',
    status: 'active',
    login: '',
    password: '',
    notes: ''
  });

  // Memoized handlers
  const handleInputChange = useCallback((field: keyof EmployeeForm, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleInputChange('name', e.target.value);
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

  const handleRoleChange = useCallback((keys: any) => {
    const roleId = Array.from(keys)[0] as string;
    handleInputChange('role_id', parseInt(roleId) || 0);
  }, [handleInputChange]);

  const handleStatusChange = useCallback((keys: any) => {
    const status = Array.from(keys)[0] as string;
    handleInputChange('status', status);
  }, [handleInputChange]);

  const generateCredentials = useCallback(() => {
    let login = '';
    if (form.name) {
      const names = form.name.toLowerCase().split(' ');
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
    
    setForm(prev => ({
      ...prev,
      login: login,
      password: password
    }));
    
    showSuccess('Логин и пароль сгенерированы');
  }, [form.name, showSuccess]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!form.city_id || !form.role_id || !form.name || !form.login || !form.password) {
      showError('Пожалуйста, заполните все обязательные поля');
      return;
    }

    try {
      setSaving(true);
      await usersApi.createEmployee(form);
      showSuccess('Сотрудник успешно создан');
      navigate('/users');
    } catch (error) {
      console.error('Error creating employee:', error);
      showError('Ошибка создания сотрудника');
    } finally {
      setSaving(false);
    }
  }, [form, showError, showSuccess, navigate]);

  const handleCancel = useCallback(() => {
    navigate('/users');
  }, [navigate]);

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
          <div className="flex items-center justify-center rounded-full bg-blue-100 text-blue-700 p-3">
            <UserPlusIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Новый сотрудник</h1>
            <p className="text-gray-600">Создание нового сотрудника</p>
          </div>
        </div>
      </div>

      {/* Form */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <UserIcon className="h-6 w-6 text-gray-600" />
          <h2 className="text-xl font-semibold">Информация о сотруднике</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <Input
                label="ФИО"
                placeholder="Введите полное имя"
                value={form.name}
                onChange={handleNameChange}
                variant="bordered"
                isRequired
                startContent={<UserIcon className="h-4 w-4 text-gray-400" />}
              />

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

              <Select
                label="Роль"
                placeholder="Выберите роль"
                selectedKeys={form.role_id ? [form.role_id.toString()] : []}
                onSelectionChange={handleRoleChange}
                variant="bordered"
                isRequired
                startContent={<ShieldCheckIcon className="h-4 w-4 text-gray-400" />}
              >
                {roles.map(role => (
                  <SelectItem key={role.id.toString()}>
                    {role.name}
                  </SelectItem>
                ))}
              </Select>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <Select
                label="Статус"
                placeholder="Выберите статус"
                selectedKeys={[form.status]}
                onSelectionChange={handleStatusChange}
                variant="bordered"
              >
                <SelectItem key="active">Активен</SelectItem>
                <SelectItem key="inactive">Неактивен</SelectItem>
                <SelectItem key="pending">Ожидает</SelectItem>
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
                      color="primary"
                      onClick={generateCredentials}
                      className="min-w-unit-20"
                    >
                      Сгенерировать
                    </Button>
                  }
                />
              </div>

              <Input
                label="Примечание"
                placeholder="Дополнительная информация"
                value={form.notes}
                onChange={handleNotesChange}
                variant="bordered"
              />
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
              {saving ? 'Сохраняю...' : 'Создать сотрудника'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default EmployeeCreatePage; 