export interface Material {
  id: number;
  coil_number: string;
  material_name: string;
  supplier?: string;
  receipt_date: string;
  qc_passed: boolean;
  created_at: string;
  updated_at: string;
}

export interface MaterialCreateRequest {
  coil_number: string;
  material_name: string;
  supplier?: string;
  receipt_date: string;
  qc_passed?: boolean;
}
