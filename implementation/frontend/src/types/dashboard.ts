// /dashboard/summary 응답
export interface DashboardStats {
  active_pallets: number;
  total_stock: number;
  today_production: number;
  reader_status: {
    connected: number;
    total: number;
  };
}

// /dashboard/process-status 응답
export interface ProcessStatus {
  process_id: number;
  process_name: string;
  production_line?: string;
  active_pallets: number;
  status_breakdown: Record<string, number>;
}

export interface ProcessStatusList {
  processes: ProcessStatus[];
  total_active_pallets: number;
  last_updated: string;
}

// /dashboard/recent-activities 응답
export interface RecentActivity {
  id: number;
  pallet_no: string;
  event_type: string;
  previous_status?: string;
  new_status: string;
  process_name?: string;
  scan_time: string;
  worker_name?: string;
  notes?: string;
}

export interface RecentActivityResponse {
  activities: RecentActivity[];
  total: number;
}
