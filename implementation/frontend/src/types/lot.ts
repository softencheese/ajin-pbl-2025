export interface Lot {
  id: number;
  lot_no: string;
  part_id: number;
  process_id: number;
  material_id: number;
  quantity: number;
  production_date: string;
  worker_name?: string;
  qc_passed: boolean;
  part: {
    part_number: string;
    part_name: string;
  };
  process: {
    process_name: string;
  };
  material: {
    coil_number: string;
  };
  created_at: string;
  updated_at: string;
}

export interface LotCreateRequest {
  lot_no: string;
  part_id: number;
  process_id: number;
  material_id: number;
  quantity: number;
  production_date: string;
  worker_name?: string;
  qc_passed?: boolean;
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
