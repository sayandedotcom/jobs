"use client"

import * as React from "react"
import { Badge } from "@workspace/ui/components/badge"
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
    <a
      href={`/jobs/${job.id}`}
      className="hover:bg-accent/50 block rounded-lg border p-4 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h3 className="leading-tight font-medium">{job.title}</h3>
          <p className="text-muted-foreground mt-1 text-sm">{job.company}</p>
        </div>
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            handleSave()
          }}
          className="text-muted-foreground hover:text-foreground shrink-0 rounded-md p-1.5 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill={saved ? "currentColor" : "none"}
            stroke="currentColor"
            strokeWidth={2}
            className="h-5 w-5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z"
            />
          </svg>
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {job.location && (
          <span className="text-muted-foreground text-xs">
            📍 {job.location}
          </span>
        )}
        {job.salary && (
          <span className="text-muted-foreground text-xs">💰 {job.salary}</span>
        )}
        {job.jobType && (
          <Badge variant="secondary" className="text-xs">
            {job.jobType}
          </Badge>
        )}
      </div>
      <p className="text-muted-foreground mt-2 line-clamp-2 text-sm">
        {job.description}
      </p>
    </a>
  )
}

export { JobCard }
