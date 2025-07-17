import React, { useMemo, useCallback, useState } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Input,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  Progress
} from '@heroui/react';
import { 
  MegaphoneIcon,
  DocumentTextIcon,
  PhoneIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  BuildingOfficeIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { useMultipleApiData } from '../hooks/useApiData';
import { useAppData } from '../contexts/AppDataContext';
import { advertisingCampaignsApi } from '../api/advertisingCampaigns';
import { requestsApi, type Request } from '../api/requests';
import { usersApi } from '../api/users';
import type { AdvertisingCampaign, City } from '../types/api';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

interface CampaignReport {
  campaignId: number;
  campaignName: string;
  cityName: string;
  phoneNumber: string;
  requestsCount: number;
  requestsCompleted: number;
  conversionRate: number;
}

interface CampaignStats {
  totalCampaigns: number;
  totalRequests: number;
  totalCompleted: number;
  averageConversion: number;
  citiesCovered: number;
  bestCampaign: CampaignReport | null;
}

interface ReportsFilters {
  search: string;
  city: string;
  minConversion: number;
}

const ReportsAdvertisingPage: React.FC = () => {
  const { cities } = useAppData();
  
  const [filters, setFilters] = useState<ReportsFilters>({
    search: '',
    city: '',
    minConversion: 0
  });

  const apiCalls = useMemo(() => ({
    campaigns: advertisingCampaignsApi.getAdvertisingCampaigns,
    requests: requestsApi.getRequests
  }), []);

  const {
    data,
    loading,
    error
  } = useMultipleApiData<{
    campaigns: AdvertisingCampaign[];
    requests: Request[];
  }>(apiCalls);

  const campaigns = data?.campaigns;
  const requests = data?.requests;

  const reports = useMemo<CampaignReport[]>(() => {
    if (!campaigns || !requests || !cities) return [];

    return campaigns.map(campaign => {
      const campaignRequests = requests.filter(req => req.advertising_campaign_id === campaign.id);
      const city = cities.find(c => c.id === campaign.city_id);
      
      const requestsCount = campaignRequests.length;
      const requestsCompleted = campaignRequests.filter(req => 
        ['completed', 'done', 'finished'].includes(req.status || '')
      ).length;
      const conversionRate = requestsCount > 0 ? (requestsCompleted / requestsCount) * 100 : 0;
      
      return {
        campaignId: campaign.id,
        campaignName: campaign.name,
        cityName: city?.name || 'Неизвестно',
        phoneNumber: campaign.phone_number || '',
        requestsCount,
        requestsCompleted,
        conversionRate
      };
    });
  }, [campaigns, requests, cities]);

  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      const matchesSearch = !filters.search || 
        report.campaignName.toLowerCase().includes(filters.search.toLowerCase()) ||
        report.cityName.toLowerCase().includes(filters.search.toLowerCase()) ||
        report.phoneNumber.includes(filters.search);
        
      const matchesCity = !filters.city || report.cityName === filters.city;
      const matchesConversion = report.conversionRate >= filters.minConversion;
      
      return matchesSearch && matchesCity && matchesConversion;
    });
  }, [reports, filters]);

  const stats = useMemo<CampaignStats>(() => {
    if (filteredReports.length === 0) {
      return {
        totalCampaigns: 0,
        totalRequests: 0,
        totalCompleted: 0,
        averageConversion: 0,
        citiesCovered: 0,
        bestCampaign: null
      };
    }

    const totalRequests = filteredReports.reduce((sum, report) => sum + report.requestsCount, 0);
    const totalCompleted = filteredReports.reduce((sum, report) => sum + report.requestsCompleted, 0);
    const averageConversion = filteredReports.length > 0 
      ? filteredReports.reduce((sum, report) => sum + report.conversionRate, 0) / filteredReports.length
      : 0;
    
    const uniqueCities = new Set(filteredReports.map(r => r.cityName)).size;
    const bestCampaign = filteredReports.reduce((best, current) => 
      !best || current.conversionRate > best.conversionRate ? current : best
    , null as CampaignReport | null);

    return {
      totalCampaigns: filteredReports.length,
      totalRequests,
      totalCompleted,
      averageConversion,
      citiesCovered: uniqueCities,
      bestCampaign
    };
  }, [filteredReports]);

  const handleSearchChange = useCallback((value: string) => {
    setFilters(prev => ({ ...prev, search: value }));
  }, []);

  const handleCityChange = useCallback((value: string) => {
    setFilters(prev => ({ ...prev, city: value }));
  }, []);

  const handleConversionChange = useCallback((value: string) => {
    setFilters(prev => ({ ...prev, minConversion: Number(value) || 0 }));
  }, []);

  const renderTableRow = useCallback((report: CampaignReport) => (
    <TableRow key={report.campaignId}>
      <TableCell>
        <div>
          <p className="font-medium">{report.campaignName}</p>
          <p className="text-sm text-gray-500 flex items-center gap-1">
            <BuildingOfficeIcon className="w-3 h-3" />
            {report.cityName}
          </p>
          {report.phoneNumber && (
            <div className="flex items-center gap-2 mt-1">
              <PhoneIcon className="h-3 w-3 text-gray-400" />
              <a 
                href={`tel:${report.phoneNumber}`}
                className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
              >
                {report.phoneNumber}
              </a>
            </div>
          )}
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-sm">Всего:</span>
            <span className="text-sm font-bold">{report.requestsCount}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Завершено:</span>
            <Chip color="success" size="sm" variant="flat">
              {report.requestsCompleted}
            </Chip>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">Конверсия:</span>
            <Chip 
              color={report.conversionRate >= 80 ? 'success' : report.conversionRate >= 60 ? 'warning' : 'danger'} 
              size="sm" 
              variant="flat"
            >
              {report.conversionRate.toFixed(1)}%
            </Chip>
          </div>
          <Progress 
            value={report.conversionRate} 
            color={report.conversionRate >= 80 ? 'success' : report.conversionRate >= 60 ? 'warning' : 'danger'}
            size="sm"
            className="w-full"
          />
        </div>
      </TableCell>
    </TableRow>
  ), []);

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Card className="bg-red-50 border-red-200">
          <CardBody>
            <p className="text-red-700">Ошибка загрузки данных: {error}</p>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center rounded-full bg-orange-100 text-orange-700 p-3">
            <MegaphoneIcon className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Отчет по рекламе</h1>
            <p className="text-gray-600">Аналитика рекламных кампаний и конверсии</p>
          </div>
        </div>
      </div>

      {/* Статистические карточки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardBody className="text-center">
            <MegaphoneIcon className="w-8 h-8 text-orange-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Кампаний</p>
            <p className="text-2xl font-bold text-orange-700">{stats.totalCampaigns}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardBody className="text-center">
            <DocumentTextIcon className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Заявок всего</p>
            <p className="text-2xl font-bold text-green-700">{stats.totalRequests}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardBody className="text-center">
            <CheckCircleIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Завершено</p>
            <p className="text-2xl font-bold text-blue-700">{stats.totalCompleted}</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardBody className="text-center">
            <ChartBarIcon className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Средняя конверсия</p>
            <p className="text-2xl font-bold text-purple-700">{stats.averageConversion.toFixed(1)}%</p>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100 border-cyan-200">
          <CardBody className="text-center">
            <BuildingOfficeIcon className="w-8 h-8 text-cyan-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">Городов</p>
            <p className="text-2xl font-bold text-cyan-700">{stats.citiesCovered}</p>
          </CardBody>
        </Card>
      </div>

      {/* Фильтры */}
      <Card className="mb-8">
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              placeholder="Поиск по названию, городу или телефону"
              startContent={<MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />}
              value={filters.search}
              onChange={(e) => handleSearchChange(e.target.value)}
              size="md"
            />
            <select
              value={filters.city}
              onChange={(e) => handleCityChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все города</option>
              {cities?.map(city => (
                <option key={city.id} value={city.name}>{city.name}</option>
              ))}
            </select>
            <Input
              type="number"
              placeholder="Минимальная конверсия (%)"
              value={filters.minConversion.toString()}
              onChange={(e) => handleConversionChange(e.target.value)}
              min="0"
              max="100"
              size="md"
            />
          </div>
        </CardBody>
      </Card>

      {/* Лучшая кампания */}
      {stats.bestCampaign && (
        <Card className="mb-8 bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-200">
          <CardBody>
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center rounded-full bg-yellow-500 text-white p-3">
                <CheckCircleIcon className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-yellow-800">Лучшая кампания</h3>
                <p className="text-yellow-700">
                  {stats.bestCampaign.campaignName} в городе {stats.bestCampaign.cityName} - 
                  конверсия {stats.bestCampaign.conversionRate.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Таблица отчетов */}
      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold">
            Детальный отчет по рекламным кампаниям ({filteredReports.length})
          </h3>
        </CardHeader>
        <CardBody>
          <Table aria-label="Отчет по рекламе">
            <TableHeader>
              <TableColumn>Кампания</TableColumn>
              <TableColumn>Заявки</TableColumn>
              <TableColumn>Эффективность</TableColumn>
            </TableHeader>
            <TableBody>
              {filteredReports.map(renderTableRow)}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
};

export default ReportsAdvertisingPage; 