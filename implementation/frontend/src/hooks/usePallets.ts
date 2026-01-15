import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { palletApi } from '../api/pallets';
import type { PalletCreateRequest } from '../types/pallet';

export function usePallets(params?: Parameters<typeof palletApi.getAll>[0]) {
  return useQuery({
    queryKey: ['pallets', params],
    queryFn: async () => {
      const response = await palletApi.getAll(params);
      return response.items;
    },
  });
}

export function usePallet(id: number) {
  return useQuery({
    queryKey: ['pallet', id],
    queryFn: () => palletApi.getById(id),
    enabled: !!id,
  });
}

export function useCreatePallet() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: PalletCreateRequest) => palletApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pallets'] });
    },
  });
}
