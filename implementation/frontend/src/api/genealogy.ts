import { apiClient } from './client';

export interface LotGenealogyItem {
  lot_number: string;
  item_code: string;
  item_type: string;
  quantity_consumed?: number;
}

export interface LotGenealogyResponse {
  lot: {
    id: number;
    lot_number: string;
    item_code: string | null;
  };
  parents: LotGenealogyItem[];
  children: LotGenealogyItem[];
}

export const genealogyApi = {
  async getByLotId(lotId: number) {
    const { data } = await apiClient.get<LotGenealogyResponse>(`/lot-genealogy/${lotId}`);
    return data;
  },
};
