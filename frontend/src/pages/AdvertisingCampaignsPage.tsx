import React, { useState, useMemo, useCallback } from 'react';
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Input,
  Button,
  Select,
  SelectItem,
  Card,
  Chip,
  Spinner,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure
} from '@heroui/react';
import { 
  PlusIcon, 
  MagnifyingGlassIcon, 
  FunnelIcon,
  SpeakerWaveIcon,
  MapPinIcon,
  PhoneIcon
} from '@heroicons/react/24/outline';
import { advertisingCampaignsApi } from '../api/advertisingCampaigns';
import { useApiData, useApiMutation } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { useNotification } from '../contexts/NotificationContext';
import type { AdvertisingCampaign, CreateAdvertisingCampaignData } from '../types/api';

// Интерфейс для фильтров
interface CampaignFilters {
  city_id: string;
  name: string;
}

const initialForm: CreateAdvertisingCampaignData = {
  city_id: 0,
  name: '',
  phone_number: '',
};

const AdvertisingCampaignsPage: React.FC = () => {
  const { cities } = useAppData();
  const { showSuccess, showError } = useNotification();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const [filters, setFilters] = useState<CampaignFilters>({ 
    city_id: '', 
    name: '' 
  });
  const [createForm, setCreateForm] = useState<CreateAdvertisingCampaignData>(initialForm);

  // Загрузка кампаний
  const getCampaigns = useCallback(() => advertisingCampaignsApi.getAdvertisingCampaigns(), []);
  
  const { 
    data: campaignsData, 
    loading: campaignsLoading, 
    refetch: refetchCampaigns 
  } = useApiData(getCampaigns, {
    errorMessage: 'Ошибка загрузки кампаний'
  });

  // Мутация для создания кампании
  const { mutate: createCampaign, loading: createLoading } = useApiMutation(
    (data: CreateAdvertisingCampaignData) => advertisingCampaignsApi.createAdvertisingCampaign(data),
    {
      successMessage: 'Кампания успешно создана',
      errorMessage: 'Ошибка создания кампании',
      onSuccess: () => {
        refetchCampaigns();
        onClose();
        setCreateForm(initialForm);
      }
    }
  );

  // Мемоизированная фильтрация кампаний
  const filteredCampaigns = useMemo(() => {
    if (!campaignsData) return [];
    
    return campaignsData.filter(campaign => {
      const matchesCity = !filters.city_id || campaign.city_id === parseInt(filters.city_id);
      const matchesName = !filters.name || campaign.name.toLowerCase().includes(filters.name.toLowerCase());
      return matchesCity && matchesName;
    });
  }, [campaignsData, filters]);

  // Статистика кампаний
  const campaignStats = useMemo(() => {
    if (!filteredCampaigns) return { total: 0, citiesCount: 0, averagePerCity: 0 };
    
    const uniqueCities = new Set(filteredCampaigns.map(c => c.city_id));
    const citiesCount = uniqueCities.size;
    const averagePerCity = citiesCount > 0 ? Math.round(filteredCampaigns.length / citiesCount) : 0;
    
    return {
      total: filteredCampaigns.length,
      citiesCount,
      averagePerCity
    };
  }, [filteredCampaigns]);

  // Мемоизированные обработчики
  const handleFilterChange = useCallback((key: keyof CampaignFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleFormChange = useCallback((key: keyof CreateAdvertisingCampaignData, value: string | number) => {
    setCreateForm(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleCreate = useCallback(() => {
    if (!createForm.city_id || !createForm.name || !createForm.phone_number) {
      showError('Заполните все поля');
      return;
    }
    createCampaign(createForm);
  }, [createForm, createCampaign, showError]);

  const getCityName = useCallback((cityId: number) => {
    const city = cities.find(c => c.id === cityId);
    return city ? city.name : '—';
  }, [cities]);

  // Мемоизированный рендер строки кампании
  const renderCampaignRow = useCallback((campaign: AdvertisingCampaign) => (
    <TableRow key={campaign.id}>
      <TableCell>{campaign.id}</TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <MapPinIcon className="h-4 w-4 text-gray-400" />
          {getCityName(campaign.city_id)}
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <SpeakerWaveIcon className="h-4 w-4 text-blue-500" />
          {campaign.name}
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <PhoneIcon className="h-4 w-4 text-green-500" />
          <a 
            href={`tel:${campaign.phone_number}`}
            className="text-blue-600 hover:text-blue-800"
          >
            {campaign.phone_number}
          </a>
        </div>
      </TableCell>
    </TableRow>
  ), [getCityName]);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Рекламные кампании</h1>
        <p className="text-gray-600 mb-4">Управление рекламными кампаниями</p>
        
        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <SpeakerWaveIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Всего кампаний</p>
                <p className="text-2xl font-bold">{campaignStats.total}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <MapPinIcon className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Городов охвачено</p>
                <p className="text-2xl font-bold text-green-600">{campaignStats.citiesCount}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <PhoneIcon className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">В среднем на город</p>
                <p className="text-2xl font-bold text-purple-600">{campaignStats.averagePerCity}</p>
              </div>
            </div>
          </Card>
        </div>
        
        {/* Фильтры */}
        <Card className="mb-4">
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
              <h3 className="text-lg font-medium">Фильтры</h3>
            </div>
            <div className="flex flex-wrap gap-4 items-center">
              <Select
                placeholder="Все города"
                selectedKeys={filters.city_id ? [filters.city_id] : []}
                onSelectionChange={(keys) => 
                  handleFilterChange('city_id', Array.from(keys)[0] as string || '')
                }
                className="max-w-xs"
                isLoading={!cities.length}
              >
                {cities.map(city => (
                  <SelectItem key={city.id}>
                    {city.name}
                  </SelectItem>
                ))}
              </Select>
              
              <Input
                placeholder="Поиск по названию..."
                value={filters.name}
                onChange={(e) => handleFilterChange('name', e.target.value)}
                className="max-w-xs"
                startContent={<MagnifyingGlassIcon className="h-4 w-4" />}
              />
              
              <Button
                color="primary"
                onClick={onOpen}
                startContent={<PlusIcon className="h-4 w-4" />}
              >
                Новая кампания
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Основная таблица */}
      <Card>
        <div className="p-4">
          <Table aria-label="Таблица рекламных кампаний">
            <TableHeader>
              <TableColumn>ID</TableColumn>
              <TableColumn>Город</TableColumn>
              <TableColumn>Название</TableColumn>
              <TableColumn>Телефон</TableColumn>
            </TableHeader>
            <TableBody
              isLoading={campaignsLoading}
              loadingContent={<Spinner />}
              emptyContent="Нет данных"
            >
              {filteredCampaigns.map(renderCampaignRow)}
            </TableBody>
          </Table>
        </div>
      </Card>

      {/* Модал создания кампании */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalContent>
          <ModalHeader>Новая рекламная кампания</ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <Select
                label="Город"
                placeholder="Выберите город"
                selectedKeys={createForm.city_id ? [createForm.city_id.toString()] : []}
                onSelectionChange={(keys) => 
                  handleFormChange('city_id', Number(Array.from(keys)[0]) || 0)
                }
                isRequired
                isLoading={!cities.length}
              >
                {cities.map(city => (
                  <SelectItem key={city.id}>
                    {city.name}
                  </SelectItem>
                ))}
              </Select>
              
              <Input
                label="Название кампании"
                placeholder="Введите название кампании"
                value={createForm.name}
                onChange={(e) => handleFormChange('name', e.target.value)}
                isRequired
              />
              
              <Input
                label="Телефон"
                placeholder="+7 (999) 999-99-99"
                value={createForm.phone_number}
                onChange={(e) => handleFormChange('phone_number', e.target.value)}
                isRequired
                startContent={<PhoneIcon className="h-4 w-4" />}
              />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onClose}>
              Отмена
            </Button>
            <Button 
              color="primary" 
              onPress={handleCreate}
              isLoading={createLoading}
              isDisabled={!createForm.city_id || !createForm.name || !createForm.phone_number}
            >
              Создать
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default AdvertisingCampaignsPage; 