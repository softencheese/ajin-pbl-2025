import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => dashboardApi.getStats(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useProcessStatus() {
  return useQuery({
    queryKey: ['dashboard', 'process-status'],
    queryFn: () => dashboardApi.getProcessStatus(),
    refetchInterval: 30000,
  });
}

export function useRecentActivities(limit: number = 20) {
  return useQuery({
    queryKey: ['dashboard', 'recent-activities', limit],
    queryFn: () => dashboardApi.getRecentActivities(limit),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}
