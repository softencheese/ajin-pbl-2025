import { apiClient } from './client';
import type { Item, ItemCreateRequest, ItemUpdateRequest, ItemListResponse } from '../types/item';

export interface ItemQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  item_type?: string;
  is_active?: boolean;
}

export const itemApi = {
  /**
   * Get all items with pagination and filters
   */
  getAll: async (params?: ItemQueryParams): Promise<ItemListResponse> => {
    const { data } = await apiClient.get<ItemListResponse>('/items', { params });
    return data;
  },

  /**
   * Get single item by ID
   */
  getById: async (id: number): Promise<Item> => {
    const { data } = await apiClient.get<Item>(`/items/${id}`);
    return data;
  },

  /**
   * Create new item
   */
  create: async (payload: ItemCreateRequest): Promise<Item> => {
    const { data } = await apiClient.post<Item>('/items', payload);
    return data;
  },

  /**
   * Update item
   */
  update: async (id: number, payload: ItemUpdateRequest): Promise<Item> => {
    const { data } = await apiClient.put<Item>(`/items/${id}`, payload);
    return data;
  },

  /**
   * Delete item
   */
  delete: async (id: number): Promise<{ success: boolean; message: string }> => {
    const { data } = await apiClient.delete<{ success: boolean; message: string }>(`/items/${id}`);
    return data;
  },
};
