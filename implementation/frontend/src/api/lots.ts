import { apiClient } from './client';
import type {
  Lot,
  LotCreateRequest,
  AssemblyLot,
  AssemblyLotCreateRequest,
  AssemblyComponent,
  AssemblyComponentCreateRequest
} from '../types/lot';

export const lotApi = {
  async getAll(params?: { search?: string; process_id?: number; part_id?: number }) {
    const { data } = await apiClient.get<Lot[]>('/lots', { params });
    return data;
  },

  async getById(id: number) {
    const { data } = await apiClient.get<Lot>(`/lots/${id}`);
    return data;
  },

  async create(payload: LotCreateRequest) {
    const { data } = await apiClient.post<Lot>('/lots', payload);
    return data;
  },

  async update(id: number, payload: Partial<LotCreateRequest>) {
    const { data } = await apiClient.put<Lot>(`/lots/${id}`, payload);
    return data;
  },

  async delete(id: number) {
    await apiClient.delete(`/lots/${id}`);
  },
};

export const assemblyLotApi = {
  async getAll(params?: { search?: string; part_id?: number }) {
    const { data } = await apiClient.get<AssemblyLot[]>('/assembly-lots', { params });
    return data;
  },

  async getById(id: number) {
    const { data } = await apiClient.get<AssemblyLot>(`/assembly-lots/${id}`);
    return data;
  },

  async create(payload: AssemblyLotCreateRequest) {
    const { data } = await apiClient.post<AssemblyLot>('/assembly-lots', payload);
    return data;
  },

  async update(id: number, payload: Partial<AssemblyLotCreateRequest>) {
    const { data } = await apiClient.put<AssemblyLot>(`/assembly-lots/${id}`, payload);
    return data;
  },

  async delete(id: number) {
    await apiClient.delete(`/assembly-lots/${id}`);
  },

  async addComponent(payload: AssemblyComponentCreateRequest) {
    const { data } = await apiClient.post<AssemblyComponent>('/assembly-lots/components', payload);
    return data;
  },

  async removeComponent(componentId: number) {
    await apiClient.delete(`/assembly-lots/components/${componentId}`);
  },
};
