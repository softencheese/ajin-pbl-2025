import { apiClient } from './client';

export interface LotGenealogyItem {
    lot_number: string;
    item_code: string;
    item_type: string;
    quantity_consumed?: number;
    process_name?: string;
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

export interface LotGenealogyWithDetails {
    id: number;
    input_lot_number: string;
    input_item_code: string;
    input_item_type: 'RAW' | 'WIP' | 'PRODUCT';
    output_lot_number: string;
    output_item_code: string;
    output_item_type: 'RAW' | 'WIP' | 'PRODUCT';
    process_name: string;
    quantity_consumed: number;
    created_at: string;
}

export interface LotGenealogyRaw {
    id: number;
    input_lot_id: number;
    output_lot_id: number;
    process_id: number;
    quantity_consumed: number;
    created_at: string;
}

export const genealogyApi = {
    async getByLotId(lotId: number) {
        const { data } = await apiClient.get<LotGenealogyResponse>(`/lot-genealogy/${lotId}`);
        return data;
    },

    async getHistory() {
        const { data } = await apiClient.get<LotGenealogyWithDetails[]>('/lot-genealogy/history');
        return data;
    },

    async getAll() {
        const { data } = await apiClient.get<LotGenealogyRaw[]>('/lot-genealogy/all');
        return data;
    },
};
