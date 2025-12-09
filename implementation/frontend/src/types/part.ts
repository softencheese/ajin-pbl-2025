export interface Part {
  id: number;
  part_number: string;
  part_name: string;
  part_spec?: string;
  vehicle_model?: string;
  is_assembly: boolean;
  is_final_product: boolean;
  created_at: string;
  updated_at: string;
}

export interface PartCreateRequest {
  part_number: string;
  part_name: string;
  part_spec?: string;
  vehicle_model?: string;
  is_assembly?: boolean;
  is_final_product?: boolean;
}
