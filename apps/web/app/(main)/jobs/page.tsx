"use client"

import * as React from "react"
import { JobCard, JobCardSkeleton } from "@/components/cards"
import {
  JobSearchBar,
  FilterSidebarProvider,
  FilterSidebar,
  sourceIdToSourceName,
} from "@/components/job-filters"
import { Button } from "@workspace/ui/components/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@workspace/ui/components/tooltip"
import { LayoutGridIcon, LoaderIcon } from "lucide-react"
import { useQueryFilters } from "@/hooks/use-query-filters"
import { useCookieState } from "@/hooks/use-cookie-state"
import { useInfiniteJobs } from "@/hooks/use-infinite-jobs"
import { source } from "@/config/source"

export default function JobsPage() {
  return (
    <React.Suspense
      fallback={
        <div className="-mt-4 flex flex-col">
          <div className="bg-background sticky top-0 z-10 -mx-4 px-4 pt-4 pb-2">
            <div className="bg-muted mx-auto h-11 w-full max-w-2xl animate-pulse rounded-md" />
            <p className="text-muted-foreground mt-3 text-sm">
              Loading filters...
            </p>
          </div>
          <div className="space-y-3 pt-2">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <JobCardSkeleton key={i} />
            ))}
          </div>
        </div>
      }
    >
      <JobsPageContent />
    </React.Suspense>
  )
}

function useInfiniteScroll(callback: () => void, enabled: boolean) {
  const sentinelRef = React.useRef<HTMLDivElement | null>(null)

  React.useEffect(() => {
    if (!enabled) return
    const sentinel = sentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) callback()
      },
      { rootMargin: "400px" }
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [callback, enabled])

  return sentinelRef
}

function JobsPageContent() {
  const {
    search,
    location,
    selectedSources,
    selectedWorkModes,
    selectedJobTypes,
    selectedExperience,
    selectedDates,
    setSearch,
    setLocation,
    setSelectedSources,
    setSelectedWorkModes,
    setSelectedJobTypes,
    setSelectedExperience,
    setSelectedDates,
    clearAll,
  } = useQueryFilters()

  const [twoColumns, setTwoColumns] = useCookieState<boolean>(
    "jobs-grid-view",
    false,
    { serialize: (v) => String(v), deserialize: (v) => v === "true" }
  )

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } =
    useInfiniteJobs({
      search: search || undefined,
      location: location || undefined,
    })

  const total = data?.total ?? 0

  const fetchMore = React.useCallback(() => {
    if (!isFetchingNextPage) fetchNextPage()
  }, [fetchNextPage, isFetchingNextPage])

  const sentinelRef = useInfiniteScroll(fetchMore, !!hasNextPage)

  const filteredJobs = React.useMemo(() => {
    return (data?.jobs ?? []).filter((job) => {
      if (selectedSources.length > 0) {
        const sourceId = job.sourceName
          ? sourceIdToSourceName(job.sourceName)
          : null
        if (!sourceId || !selectedSources.includes(sourceId)) return false
      }
      if (selectedWorkModes.length > 0) {
        const desc = job.description?.toLowerCase() ?? ""
        const title = job.title?.toLowerCase() ?? ""
        const text = `${title} ${desc}`
        const matchesWorkMode = selectedWorkModes.some((mode) =>
          text.includes(mode)
        )
        if (!matchesWorkMode) return false
      }
      if (selectedJobTypes.length > 0) {
        const desc = job.description?.toLowerCase() ?? ""
        const title = job.title?.toLowerCase() ?? ""
        const text = `${title} ${desc}`
        const matchesJobType = selectedJobTypes.some((type) =>
          text.includes(type.replace("-", " "))
        )
        if (!matchesJobType) return false
      }
      if (selectedExperience.length > 0) {
        const desc = job.description?.toLowerCase() ?? ""
        const title = job.title?.toLowerCase() ?? ""
        const text = `${title} ${desc}`
        const matchesExp = selectedExperience.some((level) =>
          text.includes(level)
        )
        if (!matchesExp) return false
      }
      if (selectedDates.length > 0 && job.postedAt) {
        const jobDate = new Date(job.postedAt)
        const jobMonthYear = jobDate.toLocaleDateString("en-US", {
          month: "long",
          year: "numeric",
        })
        if (!selectedDates.includes(jobMonthYear)) return false
      }
      if (selectedDates.length > 0 && !job.postedAt) return false
      return true
    })
  }, [
    data,
    selectedSources,
    selectedWorkModes,
    selectedJobTypes,
    selectedExperience,
    selectedDates,
  ])

  const displayTotal =
    selectedSources.length > 0 ||
    selectedWorkModes.length > 0 ||
    selectedJobTypes.length > 0 ||
    selectedExperience.length > 0 ||
    selectedDates.length > 0
      ? filteredJobs.length
      : total

  return (
    <FilterSidebarProvider>
      <div className="-mt-4 flex flex-1 flex-col">
        <div className="bg-background sticky top-0 z-10 -mx-4 px-4 pt-4 pb-2">
          <div className="mx-auto w-full max-w-2xl">
            <JobSearchBar search={search} onSearchChange={setSearch} />
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <TooltipProvider delay={300}>
              <Tooltip>
                <TooltipTrigger
                  render={
                    <Button
                      variant={twoColumns ? "default" : "outline"}
                      size="icon-sm"
                      className="shrink-0 cursor-pointer"
                      onClick={() => setTwoColumns((v) => !v)}
                      aria-label="Toggle grid view"
                    >
                      <LayoutGridIcon className="size-4" />
                    </Button>
                  }
                />
                <TooltipContent>
                  {twoColumns ? "Single column" : "Two columns"}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <p className="text-muted-foreground flex flex-wrap items-center gap-1.5 text-sm">
              <a
                href="/integrations"
                className="hover:text-foreground/80 underline underline-offset-4 transition-colors"
              >
                Last fetch 15hr ago · Next in 4h
              </a>
              <span>•</span>
              <a
                href="/integrations"
                className="hover:text-foreground/80 underline underline-offset-4 transition-colors"
              >
                {source.filter((s) => s.active).length} sources active
              </a>
              <span>•</span>
              <span>
                {isLoading
                  ? "Searching for jobs..."
                  : `${displayTotal} job${displayTotal !== 1 ? "s" : ""} found`}
              </span>
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          {isLoading ? (
            <div
              className={twoColumns ? "grid grid-cols-2 gap-3" : "space-y-3"}
            >
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <JobCardSkeleton key={i} />
              ))}
            </div>
          ) : filteredJobs.length > 0 ? (
            <div
              className={twoColumns ? "grid grid-cols-2 gap-3" : "space-y-3"}
            >
              {filteredJobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          ) : (
            <div className="text-muted-foreground py-12 text-center">
              No jobs found. Try adjusting your filters.
            </div>
          )}

          {hasNextPage && (
            <div ref={sentinelRef} className="flex justify-center py-4">
              {isFetchingNextPage && (
                <LoaderIcon className="text-muted-foreground size-5 animate-spin" />
              )}
            </div>
          )}
        </div>
      </div>
      <FilterSidebar
        location={location}
        selectedSources={selectedSources}
        selectedWorkModes={selectedWorkModes}
        selectedJobTypes={selectedJobTypes}
        selectedExperience={selectedExperience}
        selectedDates={selectedDates}
        onLocationChange={setLocation}
        onSelectedSourcesChange={setSelectedSources}
        onSelectedWorkModesChange={setSelectedWorkModes}
        onSelectedJobTypesChange={setSelectedJobTypes}
        onSelectedExperienceChange={setSelectedExperience}
        onSelectedDatesChange={setSelectedDates}
        onClearAll={clearAll}
      />
    </FilterSidebarProvider>
  )
}
