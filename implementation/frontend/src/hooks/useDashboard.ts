import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => dashboardApi.getStats(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useProcessSummary() {
  return useQuery({
    queryKey: ['dashboard', 'process-summary'],
    queryFn: () => dashboardApi.getProcessSummary(),
    refetchInterval: 30000,
  });
}

export function useRecentActivity(limit: number = 20) {
  return useQuery({
    queryKey: ['dashboard', 'recent-activity', limit],
    queryFn: () => dashboardApi.getRecentActivity(limit),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}
