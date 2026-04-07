import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/axios"
import type { UserSavedJob } from "@/lib/api-client"

export function useSavedJobs() {
  return useQuery<UserSavedJob[]>({
    queryKey: ["saved"],
    queryFn: async () => {
      const { data } = await api.get<UserSavedJob[]>("/api/saved")
      return data
    },
  })
}

export function useCreateSavedJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (listingId: string) => {
      const { data } = await api.post<UserSavedJob>("/api/saved", {
        listingId,
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved"] })
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
    },
  })
}

export function useUpdateSavedJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      savedId,
      body,
    }: {
      savedId: string
      body: { status?: string; notes?: string }
    }) => {
      const { data } = await api.patch<UserSavedJob>(
        `/api/saved/${savedId}`,
        body
      )
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved"] })
    },
  })
}

export function useDeleteSavedJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (savedId: string) => {
      await api.delete(`/api/saved/${savedId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved"] })
    },
  })
}
