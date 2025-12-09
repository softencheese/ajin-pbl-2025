export interface Process {
  id: number;
  process_code: string;
  process_name: string;
  process_order: number;
  production_line?: string;
  created_at: string;
  updated_at: string;
}

export interface ProcessCreateRequest {
  process_code: string;
  process_name: string;
  process_order: number;
  production_line?: string;
}
