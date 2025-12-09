export interface TraceNode {
  type: 'material' | 'lot' | 'assembly_lot' | 'pallet' | 'part';
  id: number;
  label: string;
  details: any;
  children?: TraceNode[];
}

export interface TraceResult {
  type: 'part' | 'lot' | 'assembly_lot' | 'pallet' | 'material';
  data: any;
  forward_trace?: TraceNode[];
  backward_trace?: TraceNode[];
}

export interface PalletHistory {
  id: number;
  pallet_id: number;
  previous_status: string;
  current_status: string;
  process_id?: number;
  location_type?: string;
  worker_name?: string;
  timestamp: string;
  process?: {
    process_name: string;
  };
}
