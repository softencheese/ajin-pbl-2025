export type PalletStatus =
  | 'Generated'
  | 'Empty'
  | 'Stock'
  | 'Consuming'
  | 'Producing'
  | 'Finished'
  | 'Deregistered'
  | 'Hold'
  | 'Defect';

export interface Pallet {
  id: number;
  pallet_no: string;
  rfid_epc: string;
  status: PalletStatus;
  tag_status?: string;
  quantity?: number;
  lot_id?: number;
  current_process_id?: number;
  lot_number?: string;
  item_code?: string;
  item_name?: string;
  item_type?: string;
  current_process_name?: string;
  tag_registered_at?: string;
  created_at: string;
  updated_at?: string;
  // Legacy fields for backward compatibility
  assembly_lot_id?: number;
  lot?: {
    lot_no: string;
    part: {
      part_number: string;
      part_name: string;
    };
  };
  registered_at?: string;
}

export interface PalletCreateRequest {
  pallet_no: string;
  rfid_epc: string;
}

export type FIFOScanStatus = 'WAITING' | 'OK' | 'VIOLATION';

export interface FIFOQueueItem {
  queue_position: number;
  pallet_id: number;
  pallet_no: string;
  rfid_epc: string;
  lot_no?: string;
  item_code?: string;
  item_name?: string;
  created_at: string;
  scan_status: FIFOScanStatus;
  scan_time?: string;
}
