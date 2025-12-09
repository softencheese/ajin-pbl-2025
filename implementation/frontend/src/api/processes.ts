import { apiClient } from './client';
import type { Process, ProcessCreateRequest } from '../types/process';

export const processApi = {
  async getAll() {
    const { data } = await apiClient.get<Process[]>('/processes');
    return data;
  },

  async getById(id: number) {
    const { data } = await apiClient.get<Process>(`/processes/${id}`);
    return data;
  },

  async create(payload: ProcessCreateRequest) {
    const { data } = await apiClient.post<Process>('/processes', payload);
    return data;
  },

  async update(id: number, payload: Partial<ProcessCreateRequest>) {
    const { data } = await apiClient.put<Process>(`/processes/${id}`, payload);
    return data;
  },

  async delete(id: number) {
    await apiClient.delete(`/processes/${id}`);
  },
};
