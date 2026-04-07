import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/axios"
import type { Listing, ListingList } from "@/lib/api-client"

export function useJobs(params?: {
  search?: string
  location?: string
  jobType?: string
  company?: string
  page?: number
  pageSize?: number
}) {
  return useQuery<ListingList>({
    queryKey: ["jobs", params],
    queryFn: async () => {
      const { data } = await api.get<ListingList>("/api/jobs", { params })
      return data
    },
  })
}

export function useJob(id: string) {
  return useQuery<Listing>({
    queryKey: ["jobs", id],
    queryFn: async () => {
      const { data } = await api.get<Listing>(`/api/jobs/${id}`)
      return data
    },
    enabled: !!id,
  })
}
