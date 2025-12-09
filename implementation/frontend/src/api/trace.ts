import { apiClient } from './client';
import type { TraceResult, PalletHistory } from '../types/trace';

export const traceApi = {
  async search(query: string) {
    const { data } = await apiClient.get<TraceResult>('/trace/search', {
      params: { q: query }
    });
    return data;
  },

  async getPalletHistory(palletId: number) {
    const { data } = await apiClient.get<PalletHistory[]>(`/trace/pallet/${palletId}/history`);
    return data;
  },

  async getLotHistory(lotId: number) {
    const { data } = await apiClient.get(`/trace/lot/${lotId}/history`);
    return data;
  },
};
