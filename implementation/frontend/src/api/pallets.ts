import { apiClient } from './client';
import type { Pallet, PalletCreateRequest, FIFOQueueItem } from '../types/pallet';

export const palletApi = {
  async getAll(params?: {
    status?: string;
    process_id?: number;
    lot_id?: number;
    search?: string;
    page?: number;
    per_page?: number;
  }) {
    const { data } = await apiClient.get<{
      items: Pallet[];
      total: number;
      page: number;
      per_page: number;
      pages: number;
    }>('/pallets', { params });
    return data;
  },

  async getById(id: number) {
    const { data } = await apiClient.get<Pallet>(`/pallets/${id}`);
    return data;
  },

  async create(payload: PalletCreateRequest) {
    const { data } = await apiClient.post<Pallet>('/pallets', payload);
    return data;
  },

  async linkLot(id: number, lotId: number) {
    const { data } = await apiClient.put(`/pallets/${id}/link-lot`, { lot_id: lotId });
    return data;
  },

  async updateStatus(id: number, status: string, reason?: string) {
    const { data } = await apiClient.put(`/pallets/${id}/status`, { status, reason });
    return data;
  },

  async getFIFOQueue() {
    const { data } = await apiClient.get<{
      items: FIFOQueueItem[];
      total: number;
    }>('/pallets/fifo-queue');
    return data;
  },
};
