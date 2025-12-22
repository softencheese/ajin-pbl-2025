export interface Lot {
  id: number;
  lot_number: string;
  barcode?: string;
  item_id: number;
  quantity: number;
  initial_quantity: number;
  status: string;
  production_date: string;
  process_id?: number;
  supplier?: string;
  worker_name?: string;
  qc_passed: boolean;
  notes?: string;
  item?: {
    id: number;
    item_code: string;
    item_name: string;
    item_type: string;
  };
  process_name?: string;
  created_at: string;
  updated_at?: string;
}

export interface InputLotInfo {
  lot_id: number;
  quantity_consumed: number;
}

export interface LotCreateRequest {
  item_id: number;
  process_id: number;
  quantity: number;
  production_date: string;
  worker_name?: string;
  qc_passed?: boolean;
  barcode?: string;
  notes?: string;
  supplier?: string;
  palette_capacity?: number;
  input_lots?: InputLotInfo[];
}

export interface AssemblyLot {
  id: number;
  lot_no: string;
  part_id: number;
  assembly_date: string;
  quantity: number;
  worker_name?: string;
  qc_passed: boolean;
  part: {
    part_number: string;
    part_name: string;
  };
  components?: AssemblyComponent[];
  created_at: string;
  updated_at: string;
}

export interface AssemblyLotCreateRequest {
  lot_no: string;
  part_id: number;
  assembly_date: string;
  quantity: number;
  worker_name?: string;
  qc_passed?: boolean;
}

export interface AssemblyComponent {
  id: number;
  assembly_lot_id: number;
  component_lot_id?: number;
  component_assembly_lot_id?: number;
  quantity_per_unit: number;
  total_quantity: number;
  component_lot?: {
    lot_no: string;
    part: {
      part_number: string;
      part_name: string;
    };
  };
  component_assembly_lot?: {
    lot_no: string;
    part: {
      part_number: string;
      part_name: string;
    };
  };
}

export interface AssemblyComponentCreateRequest {
  assembly_lot_id: number;
  component_lot_id?: number;
  component_assembly_lot_id?: number;
  quantity_per_unit: number;
  total_quantity: number;
}
