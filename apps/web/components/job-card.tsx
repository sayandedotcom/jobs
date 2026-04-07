"use client"

import * as React from "react"
import {
  BookmarkIcon,
  MapPinIcon,
  BriefcaseIcon,
  DollarSignIcon,
} from "lucide-react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { Badge } from "@workspace/ui/components/badge"
import { Button } from "@workspace/ui/components/button"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { api, type Listing } from "@/lib/api-client"

function JobCard({ job }: { job: Listing }) {
  const [saved, setSaved] = React.useState(job.isSaved)

  const handleSave = async () => {
    try {
      if (!saved) {
        await api.saved.create(job.id)
        setSaved(true)
      } else {
        setSaved(false)
      }
    } catch {
      // ignore
    }
  }

  return (
    <Card className="hover:bg-accent/50 transition-colors">
      <a href={`/jobs/${job.id}`} className="block">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <CardTitle className="leading-tight">{job.title}</CardTitle>
              <p className="text-muted-foreground mt-1 text-sm">
                {job.company}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                handleSave()
              }}
              aria-label={saved ? "Unsave job" : "Save job"}
            >
              <BookmarkIcon
                className="size-4"
                fill={saved ? "currentColor" : "none"}
              />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2">
            {job.location && (
              <span className="text-muted-foreground flex items-center gap-1 text-xs">
                <MapPinIcon className="size-3" />
                {job.location}
              </span>
            )}
            {job.salary && (
              <span className="text-muted-foreground flex items-center gap-1 text-xs">
                <DollarSignIcon className="size-3" />
                {job.salary}
              </span>
            )}
            {job.jobType && (
              <Badge variant="secondary" className="text-xs">
                <BriefcaseIcon className="size-3" />
                {job.jobType}
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground mt-2 line-clamp-2 text-sm">
            {job.description}
          </p>
        </CardContent>
      </a>
    </Card>
  )
}

function JobCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/3" />
          </div>
          <Skeleton className="size-7 shrink-0 rounded-md" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </CardContent>
    </Card>
  )
}

export { JobCard, JobCardSkeleton }
