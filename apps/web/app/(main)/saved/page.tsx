"use client"

import * as React from "react"
import { api } from "@/lib/api-client"
import { authClient } from "@/lib/auth-client"
import { BookmarkIcon, LayoutGridIcon } from "lucide-react"
import { Button } from "@workspace/ui/components/button"
import { Separator } from "@workspace/ui/components/separator"
import { JobCard, JobCardSkeleton } from "@/components/cards"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@workspace/ui/components/tooltip"
import { useCookieState } from "@/hooks/use-cookie-state"
import type { Listing } from "@/lib/api-client"

export default function SavedPage() {
  const { data: session } = authClient.useSession()
  const [jobs, setJobs] = React.useState<Listing[]>([])
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    api.saved
      .list()
      .then((saved) => saved.map((s) => s.listing))
      .then(setJobs)
      .finally(() => setLoading(false))
  }, [])

  const [twoColumns, setTwoColumns] = useCookieState<boolean>(
    "saved-grid-view",
    false,
    { serialize: (v) => String(v), deserialize: (v) => v === "true" }
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center">
        <h1 className="text-2xl font-bold">Saved Jobs</h1>
      </div>
      <Separator />

      {loading ? (
        <div className={twoColumns ? "grid grid-cols-2 gap-3" : "space-y-3"}>
          {[1, 2, 3, 4, 5].map((i) => (
            <JobCardSkeleton key={i} />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-muted-foreground flex flex-col items-center gap-4 py-12 text-center">
          <BookmarkIcon className="size-12 opacity-20" />
          <p>No saved jobs yet. Browse jobs and save the ones you like.</p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
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
            <p className="text-muted-foreground text-sm">
              {jobs.length} saved job{jobs.length !== 1 ? "s" : ""}
            </p>
          </div>
          <div className={twoColumns ? "grid grid-cols-2 gap-3" : "space-y-3"}>
            {jobs.map((job) => (
              <JobCard key={job.id} job={{ ...job, isSaved: true }} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
