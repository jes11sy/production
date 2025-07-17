import { apiClient } from './client';
import type { AdvertisingCampaign } from '../types/api';

export interface CreateAdvertisingCampaign {
  city_id: number;
  name: string;
  phone_number: string;
}

export interface UpdateAdvertisingCampaign {
  city_id?: number;
  name?: string;
  phone_number?: string;
}

export const advertisingCampaignsApi = {
  getAdvertisingCampaigns: async (): Promise<AdvertisingCampaign[]> => {
    const response = await apiClient.get('/requests/advertising-campaigns/');
    return response.data;
  },
  createAdvertisingCampaign: async (data: CreateAdvertisingCampaign): Promise<AdvertisingCampaign> => {
    const response = await apiClient.post('/requests/advertising-campaigns/', data);
    return response.data;
  },
  updateAdvertisingCampaign: async (id: number, data: UpdateAdvertisingCampaign): Promise<AdvertisingCampaign> => {
    const response = await apiClient.put(`/requests/advertising-campaigns/${id}/`, data);
    return response.data;
  },
  deleteAdvertisingCampaign: async (id: number): Promise<void> => {
    await apiClient.delete(`/requests/advertising-campaigns/${id}/`);
  },
}; 