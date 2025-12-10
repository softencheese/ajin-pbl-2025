import { apiClient } from './client';
import type { Material, MaterialCreateRequest } from '../types/material';

interface MaterialListResponse {
  items: Material[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export const materialApi = {
  async getAll(params?: { search?: string; qc_passed?: boolean }) {
    const { data } = await apiClient.get<MaterialListResponse>('/materials', { params });
    return data.items;
  },

  async getById(id: number) {
    const { data } = await apiClient.get<Material>(`/materials/${id}`);
    return data;
  },

  async create(payload: MaterialCreateRequest) {
    const { data } = await apiClient.post<Material>('/materials', payload);
    return data;
  },

  async update(id: number, payload: Partial<MaterialCreateRequest>) {
    const { data } = await apiClient.put<Material>(`/materials/${id}`, payload);
    return data;
  },

  async delete(id: number) {
    await apiClient.delete(`/materials/${id}`);
  },
};
