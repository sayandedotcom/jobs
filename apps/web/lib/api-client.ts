const API_BASE = process.env.NEXT_PUBLIC_API_URL || ""

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>
}

async function apiFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { params, ...init } = options

  const url = new URL(`${API_BASE}${path}`, "http://localhost:3000")
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const res = await fetch(url.toString(), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  })

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export interface Listing {
  id: string
  title: string
  company: string
  description: string
  location: string | null
  salary: string | null
  url: string | null
  jobType: string | null
  applyUrl: string | null
  postedAt: string | null
  createdAt: string
  isSaved: boolean
}

export interface ListingList {
  jobs: Listing[]
  total: number
  page: number
  pageSize: number
}

export interface UserSavedJob {
  id: string
  listingId: string
  status: string
  notes: string | null
  listing: Listing
  createdAt: string
}

export interface SavedSearch {
  id: string
  keywords: string | null
  location: string | null
  jobType: string | null
  isActive: boolean
  createdAt: string
}

export interface Agent {
  id: string
  userId: string
  name: string
  jobTitle: string
  skills: string[]
  location: string | null
  openToRelocate: boolean
  experienceLevel: string | null
  salaryMin: number | null
  salaryMax: number | null
  jobType: string | null
  sources: string[]
  scanIntervalMinutes: number
  isActive: boolean
  lastRunAt: string | null
  nextRunAt: string | null
  createdAt: string
  updatedAt: string
  totalResults: number
  unviewedResults: number
  latestRunStatus: string | null
}

export interface AgentRun {
  id: string
  agentId: string
  status: string
  postsScanned: number
  jobsFound: number
  newJobs: number
  startedAt: string
  finishedAt: string | null
  error: string | null
}

export interface AgentResult {
  id: string
  agentId: string
  listingId: string
  relevanceScore: number
  matchReason: string | null
  isViewed: boolean
  createdAt: string
  listing: Listing
}

export const api = {
  jobs: {
    list: (params?: {
      search?: string
      location?: string
      jobType?: string
      company?: string
      page?: number
      pageSize?: number
    }) =>
      apiFetch<ListingList>("/api/jobs", {
        params: params as Record<string, string | number | undefined>,
      }),

    get: (id: string) => apiFetch<Listing>(`/api/jobs/${id}`),
  },

  saved: {
    list: () => apiFetch<UserSavedJob[]>("/api/saved"),

    create: (listingId: string) =>
      apiFetch<UserSavedJob>("/api/saved", {
        method: "POST",
        body: JSON.stringify({ listingId }),
      }),

    update: (savedId: string, data: { status?: string; notes?: string }) =>
      apiFetch<UserSavedJob>(`/api/saved/${savedId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    delete: (savedId: string) =>
      apiFetch<void>(`/api/saved/${savedId}`, {
        method: "DELETE",
      }),
  },

  searches: {
    list: () => apiFetch<SavedSearch[]>("/api/searches"),

    create: (data: {
      keywords?: string
      location?: string
      jobType?: string
    }) =>
      apiFetch<SavedSearch>("/api/searches", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    delete: (searchId: string) =>
      apiFetch<void>(`/api/searches/${searchId}`, {
        method: "DELETE",
      }),
  },

  agents: {
    list: () => apiFetch<Agent[]>("/api/agents"),

    get: (agentId: string) => apiFetch<Agent>(`/api/agents/${agentId}`),

    create: (data: {
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
    }) =>
      apiFetch<Agent>("/api/agents", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (
      agentId: string,
      data: {
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
      }
    ) =>
      apiFetch<Agent>(`/api/agents/${agentId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    delete: (agentId: string) =>
      apiFetch<void>(`/api/agents/${agentId}`, {
        method: "DELETE",
      }),

    results: (agentId: string, params?: { page?: number; pageSize?: number }) =>
      apiFetch<AgentResult[]>(`/api/agents/${agentId}/results`, {
        params: { ...params },
      }),

    runs: (agentId: string, limit?: number) =>
      apiFetch<AgentRun[]>(`/api/agents/${agentId}/runs`, {
        params: { limit },
      }),

    trigger: (agentId: string) =>
      apiFetch<AgentRun>(`/api/agents/${agentId}/trigger`, {
        method: "POST",
      }),

    markViewed: (agentId: string, resultId: string) =>
      apiFetch<void>(`/api/agents/${agentId}/results/${resultId}/view`, {
        method: "PATCH",
      }),
  },
}
