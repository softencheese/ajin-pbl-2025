export type LocationType = 'IN' | 'OUT' | 'HOLD' | 'DEFECT' | 'FINISH' | 'RETURN';

export interface ReaderLocation {
  id: number;
  port_name: string;
  process_id: number;
  location_type: LocationType;
  description?: string;
  is_active: boolean;
  process?: {
    process_name: string;
    process_code: string;
  };
  is_connected?: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReaderLocationCreateRequest {
  port_name: string;
  process_id: number;
  location_type: LocationType;
  description?: string;
  is_active?: boolean;
}
