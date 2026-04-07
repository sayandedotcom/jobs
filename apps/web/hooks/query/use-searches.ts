import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/axios"
import type { SavedSearch } from "@/lib/api-client"

export function useSavedSearches() {
  return useQuery<SavedSearch[]>({
    queryKey: ["searches"],
    queryFn: async () => {
      const { data } = await api.get<SavedSearch[]>("/api/searches")
      return data
    },
  })
}

export function useCreateSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: {
      keywords?: string
      location?: string
      jobType?: string
    }) => {
      const { data } = await api.post<SavedSearch>("/api/searches", body)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["searches"] })
    },
  })
}

export function useDeleteSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (searchId: string) => {
      await api.delete(`/api/searches/${searchId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["searches"] })
    },
  })
}
