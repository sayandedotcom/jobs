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

export const api = {
  jobs: {
    list: (params?: {
      search?: string
      location?: string
      jobType?: string
      company?: string
      page?: number
      pageSize?: number
      userId?: string
    }) =>
      apiFetch<ListingList>("/api/jobs", {
        params: params as Record<string, string | number | undefined>,
      }),

    get: (id: string) => apiFetch<Listing>(`/api/jobs/${id}`),
  },

  saved: {
    list: (userId: string) =>
      apiFetch<UserSavedJob[]>("/api/saved", { params: { userId } }),

    create: (listingId: string, userId: string) =>
      apiFetch<UserSavedJob>("/api/saved", {
        method: "POST",
        params: { userId },
        body: JSON.stringify({ listingId }),
      }),

    update: (
      savedId: string,
      userId: string,
      data: { status?: string; notes?: string }
    ) =>
      apiFetch<UserSavedJob>(`/api/saved/${savedId}`, {
        method: "PATCH",
        params: { userId },
        body: JSON.stringify(data),
      }),

    delete: (savedId: string, userId: string) =>
      apiFetch<void>(`/api/saved/${savedId}`, {
        method: "DELETE",
        params: { userId },
      }),
  },

  searches: {
    list: (userId: string) =>
      apiFetch<SavedSearch[]>("/api/searches", { params: { userId } }),

    create: (
      userId: string,
      data: { keywords?: string; location?: string; jobType?: string }
    ) =>
      apiFetch<SavedSearch>("/api/searches", {
        method: "POST",
        params: { userId },
        body: JSON.stringify(data),
      }),

    delete: (searchId: string, userId: string) =>
      apiFetch<void>(`/api/searches/${searchId}`, {
        method: "DELETE",
        params: { userId },
      }),
  },
}
