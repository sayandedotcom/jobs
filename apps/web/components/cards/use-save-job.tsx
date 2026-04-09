"use client"

import * as React from "react"
import { BookmarkIcon } from "lucide-react"
import { Button } from "@workspace/ui/components/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@workspace/ui/components/tooltip"
import { api, type Listing } from "@/lib/api-client"
import { toast } from "sonner"
import { useMutation, useQueryClient } from "@tanstack/react-query"

type JobsQueryData = {
  pages: {
    jobs: Listing[]
    total: number
    page: number
    pageSize: number
  }[]
  pageParams: number[]
}

function patchJobInCache(
  data: JobsQueryData | undefined,
  jobId: string,
  isSaved: boolean
): JobsQueryData | undefined {
  if (!data) return data
  return {
    ...data,
    pages: data.pages.map((page) => ({
      ...page,
      jobs: page.jobs.map((j) => (j.id === jobId ? { ...j, isSaved } : j)),
    })),
  }
}

function patchAllJobsQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  jobId: string,
  isSaved: boolean
) {
  queryClient
    .getQueryCache()
    .findAll({ queryKey: ["jobs"] })
    .forEach((query) => {
      query.setData(
        patchJobInCache(
          query.state.data as JobsQueryData | undefined,
          jobId,
          isSaved
        )
      )
    })
}

export function useSaveJob(job: Listing) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async (save: boolean) => {
      if (save) {
        await api.saved.create(job.id)
      } else {
        await api.saved.deleteByListing(job.id)
      }
    },
    onMutate: async (save) => {
      await queryClient.cancelQueries({ queryKey: ["jobs"] })
      patchAllJobsQueries(queryClient, job.id, save)
      toast.success(save ? "Job bookmarked" : "Removed from bookmarks")
    },
    onError: (_err, save) => {
      patchAllJobsQueries(queryClient, job.id, !save)
      toast.error("Failed to update bookmark")
    },
  })

  const handleSave = React.useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      mutation.mutate(!job.isSaved)
    },
    [mutation, job.isSaved]
  )

  return { saved: job.isSaved, handleSave }
}

export function SaveButton({
  saved,
  onClick,
}: {
  saved: boolean
  onClick: (e: React.MouseEvent) => void
}) {
  return (
    <TooltipProvider delay={300}>
      <Tooltip>
        <TooltipTrigger
          render={
            <Button
              variant="ghost"
              size="icon"
              onClick={onClick}
              aria-label={saved ? "Remove bookmark" : "Add bookmark"}
              className="cursor-pointer"
            >
              <BookmarkIcon
                className="size-5"
                fill={saved ? "currentColor" : "none"}
              />
            </Button>
          }
        />
        <TooltipContent>
          {saved ? "Remove from bookmarks" : "Add bookmark"}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
