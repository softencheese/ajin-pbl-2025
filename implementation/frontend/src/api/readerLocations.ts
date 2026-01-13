import { apiClient } from './client';
import type { ReaderLocation, ReaderLocationCreateRequest } from '../types/readerLocation';

export const readerLocationApi = {
  async getAll(params?: { process_id?: number; is_active?: boolean }) {
    const { data } = await apiClient.get<ReaderLocation[]>('/reader-locations', { params });
    return data;
  },

  async getById(id: number) {
    const { data } = await apiClient.get<ReaderLocation>(`/reader-locations/${id}`);
    return data;
  },

  async create(payload: ReaderLocationCreateRequest) {
    const { data } = await apiClient.post<ReaderLocation>('/reader-locations', payload);
    return data;
  },

  async update(id: number, payload: Partial<ReaderLocationCreateRequest>) {
    const { data } = await apiClient.put<ReaderLocation>(`/reader-locations/${id}`, payload);
    return data;
  },

  async delete(id: number) {
    await apiClient.delete(`/reader-locations/${id}`);
  },

  //UI 테스트 위해서 만든 코드 
  async testConnection(portName: string) {
    const { data } = await apiClient.post<{ success: boolean; message: string; data?: any }>(
      '/reader-locations/test-connection',
      { port_name: portName }
    );
    return data;
  },
};
