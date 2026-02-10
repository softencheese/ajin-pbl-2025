import { apiClient } from './client';
import type { DashboardStats, ProcessStatusList, RecentActivityResponse } from '../types/dashboard';

export const dashboardApi = {
  async getStats() {
    const { data } = await apiClient.get<DashboardStats>('/dashboard/summary');
    return data;
  },

  async getProcessStatus() {
    const { data } = await apiClient.get<ProcessStatusList>('/dashboard/process-status');
    return data;
  },

  async getRecentActivities(limit: number = 20) {
    const { data } = await apiClient.get<RecentActivityResponse>('/dashboard/recent-activities', {
      params: { limit }
    });
    return data;
  },
};
