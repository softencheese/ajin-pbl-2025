export type ItemType = 'RAW' | 'WIP' | 'PRODUCT';

export interface Item {
  id: number;
  item_code: string;
  item_name: string;
  item_type: ItemType;
  unit: string;
  spec?: string;
  vehicle_model?: string;
  default_supplier?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ItemCreateRequest {
  item_code: string;
  item_name: string;
  item_type: ItemType;
  unit?: string;
  spec?: string;
  vehicle_model?: string;
  default_supplier?: string;
}

export interface ItemUpdateRequest {
  item_name?: string;
  item_type?: ItemType;
  unit?: string;
  spec?: string;
  vehicle_model?: string;
  default_supplier?: string;
  is_active?: boolean;
}

export interface ItemListResponse {
  items: Item[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
