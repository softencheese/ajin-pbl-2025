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
  lot_id?: number;
  assembly_lot_id?: number;
  current_process_id?: number;
  lot?: {
    lot_no: string;
    part: {
      part_number: string;
      part_name: string;
    };
  };
  registered_at: string;
  updated_at: string;
}

export interface PalletCreateRequest {
  pallet_no: string;
  rfid_epc: string;
}
