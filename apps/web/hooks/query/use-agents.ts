import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/axios"
import type { Agent, AgentRun, AgentResult } from "@/lib/api-client"

export function useAgents() {
  return useQuery<Agent[]>({
    queryKey: ["agents"],
    queryFn: async () => {
      const { data } = await api.get<Agent[]>("/api/agents")
      return data
    },
  })
}

export function useAgent(agentId: string) {
  return useQuery<Agent>({
    queryKey: ["agents", agentId],
    queryFn: async () => {
      const { data } = await api.get<Agent>(`/api/agents/${agentId}`)
      return data
    },
    enabled: !!agentId,
  })
}

export function useCreateAgent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: {
      name: string
      jobTitle: string
      skills?: string[]
      location?: string
      openToRelocate?: boolean
      experienceLevel?: string
      salaryMin?: number
      salaryMax?: number
      jobType?: string
      sources?: string[]
      scanIntervalMinutes?: number
    }) => {
      const { data } = await api.post<Agent>("/api/agents", body)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })
}

export function useUpdateAgent(agentId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: {
      name?: string
      jobTitle?: string
      skills?: string[]
      location?: string
      openToRelocate?: boolean
      experienceLevel?: string
      salaryMin?: number
      salaryMax?: number
      jobType?: string
      sources?: string[]
      scanIntervalMinutes?: number
      isActive?: boolean
    }) => {
      const { data } = await api.patch<Agent>(`/api/agents/${agentId}`, body)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      queryClient.invalidateQueries({ queryKey: ["agents", agentId] })
    },
  })
}

export function useDeleteAgent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (agentId: string) => {
      await api.delete(`/api/agents/${agentId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })
}

export function useAgentResults(
  agentId: string,
  params?: { page?: number; pageSize?: number }
) {
  return useQuery<AgentResult[]>({
    queryKey: ["agents", agentId, "results", params],
    queryFn: async () => {
      const { data } = await api.get<AgentResult[]>(
        `/api/agents/${agentId}/results`,
        { params }
      )
      return data
    },
    enabled: !!agentId,
  })
}

export function useAgentRuns(agentId: string, limit?: number) {
  return useQuery<AgentRun[]>({
    queryKey: ["agents", agentId, "runs", limit],
    queryFn: async () => {
      const { data } = await api.get<AgentRun[]>(
        `/api/agents/${agentId}/runs`,
        { params: { limit } }
      )
      return data
    },
    enabled: !!agentId,
  })
}

export function useTriggerAgentRun(agentId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<AgentRun>(
        `/api/agents/${agentId}/trigger`
      )
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents", agentId] })
      queryClient.invalidateQueries({
        queryKey: ["agents", agentId, "runs"],
      })
    },
  })
}

export function useMarkResultViewed(agentId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (resultId: string) => {
      await api.patch(`/api/agents/${agentId}/results/${resultId}/view`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["agents", agentId, "results"],
      })
    },
  })
}
