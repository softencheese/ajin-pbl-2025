import { apiClient } from './client';
import type { Pallet, PalletCreateRequest } from '../types/pallet';

export const palletApi = {
  async getAll(params?: { status?: string; process_id?: number; search?: string }) {
    const { data } = await apiClient.get<Pallet[]>('/pallets', { params });
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
};
