"use client"

import { useInfiniteQuery } from "@tanstack/react-query"
import { api, type Listing, type ListingList } from "@/lib/api-client"

const PAGE_SIZE = 20

type JobsParams = {
  search?: string
  location?: string
}

type InfiniteJobsData = {
  jobs: Listing[]
  total: number
}

async function fetchJobsPage(
  params: JobsParams,
  page: number
): Promise<ListingList> {
  return api.jobs.list({
    search: params.search,
    location: params.location,
    page,
    pageSize: PAGE_SIZE,
  })
}

export function useInfiniteJobs(params: JobsParams) {
  return useInfiniteQuery<
    ListingList,
    Error,
    InfiniteJobsData,
    string[],
    number
  >({
    queryKey: ["jobs", params.search ?? "", params.location ?? ""],
    queryFn: ({ pageParam }) => fetchJobsPage(params, pageParam),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const totalPages = Math.ceil(lastPage.total / PAGE_SIZE)
      return lastPage.page < totalPages ? lastPage.page + 1 : undefined
    },
    select: (data) => ({
      jobs: data.pages.flatMap((page) => page.jobs),
      total: data.pages[data.pages.length - 1]?.total ?? 0,
    }),
  })
}
