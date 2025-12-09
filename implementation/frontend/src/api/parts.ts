import { apiClient } from './client';
import type { Part, PartCreateRequest } from '../types/part';

export const partApi = {
  async getAll(params?: { search?: string; is_assembly?: boolean; is_final_product?: boolean }) {
    const { data } = await apiClient.get<Part[]>('/parts', { params });
    return data;
  },

  async getById(id: number) {
    const { data } = await apiClient.get<Part>(`/parts/${id}`);
    return data;
  },

  async create(payload: PartCreateRequest) {
    const { data} = await apiClient.post<Part>('/parts', payload);
    return data;
  },

  async update(id: number, payload: Partial<PartCreateRequest>) {
    const { data } = await apiClient.put<Part>(`/parts/${id}`, payload);
    return data;
  },

  async delete(id: number) {
    await apiClient.delete(`/parts/${id}`);
  },
};
