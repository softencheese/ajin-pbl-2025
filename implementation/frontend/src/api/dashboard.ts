import { apiClient } from './client';
import type { DashboardStats, ProcessSummary, RecentActivity } from '../types/dashboard';

export const dashboardApi = {
  async getStats() {
    const { data } = await apiClient.get<DashboardStats>('/dashboard/stats');
    return data;
  },

  async getProcessSummary() {
    const { data } = await apiClient.get<ProcessSummary[]>('/dashboard/process-summary');
    return data;
  },

  async getRecentActivity(limit: number = 20) {
    const { data } = await apiClient.get<RecentActivity[]>('/dashboard/recent-activity', {
      params: { limit }
    });
    return data;
  },
};
