export interface DashboardStats {
  total_pallets: number;
  stock_pallets: number;
  producing_pallets: number;
  consuming_pallets: number;
  finished_pallets: number;
  hold_pallets: number;
  defect_pallets: number;
  total_lots: number;
  total_assembly_lots: number;
}

export interface ProcessSummary {
  process_id: number;
  process_name: string;
  pallet_count: number;
  lot_count: number;
}

export interface RecentActivity {
  id: number;
  timestamp: string;
  pallet_no: string;
  event_type: string;
  process_name?: string;
  status?: string;
  description: string;
}
